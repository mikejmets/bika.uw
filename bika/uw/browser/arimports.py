# -*- coding: utf-8 -*-

import csv
import json
import os
import pprint
import types
import re

from DateTime import DateTime
from Products.Archetypes.event import ObjectEditedEvent
from Products.Archetypes.event import ObjectInitializedEvent
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import _createObjectByType
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from UserDict import UserDict
from bika.lims import bikaMessageFactory as _
from bika.lims.browser import BrowserView
from bika.lims.utils import tmpID
from bika.lims.utils.analysisrequest import create_analysisrequest
from collective.progressbar.events import InitialiseProgressBar
from collective.progressbar.events import ProgressBar
from collective.progressbar.events import ProgressState
from collective.progressbar.events import UpdateProgressEvent
from plone.app.layout.globals.interfaces import IViewView
from plone.protect import CheckAuthenticator
from zope.container.contained import ObjectAddedEvent
from zope.container.contained import notifyContainerModified
from zope.event import notify
from zope.interface import implements
from zope.lifecycleevent import ObjectCreatedEvent

from bika.uw import logger


class ClientARImportAddView(BrowserView):
    implements(IViewView)
    template = ViewPageTemplateFile('templates/arimport_add_form.pt')

    def __init__(self, context, request):
        super(ClientARImportAddView, self).__init__(context, request)
        self.bika_setup = getToolByName(context, "bika_setup")
        self.portal_workflow = getToolByName(context, "portal_workflow")
        self.context = context
        self.request = request
        self.data = None

        # used to track the last profile found in the input
        self.profile = None

    def __call__(self):
        CheckAuthenticator(self.request.form)

        if self.form_get('submitted'):
            csvfile = self.form_get('csvfile')
            if not csvfile:
                self.statusmessage("No input CSV file was selected", "warning")
                return self.redirect(self.request.getURL())

            check_mode = self.form_get('check')

            if check_mode == "1":
                data = self.check_import_data()
                if not data:
                    self.statusmessage("Error while testing import data",
                                       "warning")
                    return self.redirect(self.request.getURL())
                valid = data['valid']
                if valid:
                    self.statusmessage("Import Data Valid", "info")
                else:
                    for error in data['errors']:
                        self.statusmessage(error, "error")
                self.data = pprint.pformat(data)
                return self.template()

            data = self._import_file(csvfile)
            if data['success']:
                self.statusmessage(_("Import Successful"), "info")
                url = self.urljoin(self.context.absolute_url(), "samples")
            else:
                for error in data['errors']:
                    self.statusmessage(error, "error")
                url = self.urljoin(self.request.getURL())
            return self.redirect(url)

        return self.template()

    def urljoin(self, *args):
        """simple urljoin
        """
        return "/".join(args)

    def check_import_data(self):
        """Return the parsed data as JSON
        """
        csvfile = self.form_get('csvfile')
        if not csvfile:
            return None
        data = self._prepare_import_data(csvfile)
        return data

    def redirect(self, url):
        """Write a redirect JavaScript to the given URL
        """
        url_script = "<script>document.location.href='{0}'</script>".format(url)
        return self.request.response.write(url_script)

    def _prepare_import_data(self, csvfile):
        """Prepare data for import

            - Checks data integrity
            - Extracts the known fields from the Spreadsheet
            - Maps Spreadsheet fields to Schema names
            - Fetch objects if they exist
        """
        _data = {
            "valid": True,
            "errors": [],
        }

        # parse the CSV data into the interanl data structure
        import_data = ImportData(csvfile)
        _data['import_data'] = import_data

        # remember the csvfile
        _data['csvfile'] = csvfile

        # Validate the import data
        valid = import_data.validate()
        if type(valid) in types.StringTypes:
            _data['valid'] = False
            _data['errors'].append(valid)

        # Client Handling
        client_id = self.form_get("ClientID")
        client = self.get_client_by_id(client_id)
        if client is None:
            _data['valid'] = False
            msg = "Could not find Client {0}".format(client_id)
            _data['errors'].append(msg)

        # Store the client data to the output data
        _data['client'] = {
            "id": client_id,
            "title": client and client.Title() or "Client not Found",
            "obj": client,
        }

        # Parse the known fields from the Spreadsheet
        #
        # Note: The variable names refer to the spreadsheet cells, e.g.:
        #       _2B is the cell at column B row 2.
        #
        # File name, Client name, Client ID, Contact, Client Order Number,
        # Client Reference
        _2B, _2C, _2D, _2E, _2F, _2G = import_data.get_data("header")[:6]
        # title, BatchID, description, ClientBatchID, ReturnSampleToClient
        _4B, _4C, _4D, _4E, _4F = import_data.get_data("batch_header")[:5]
        # Client Comment, Lab Comment
        _6B, _6C = import_data.get_data("batch_meta")[:2]
        # DateSampled, Media, SamplePoint, Activity Sampled
        _10B, _10C, _10D, _10E = import_data.get_data("samples_meta")[:4]

        # Check for valid sample Type
        sample_type = self.get_sample_type_by_name(_10C)
        if sample_type is None:
            _data['valid'] = False
            msg = "Could not find Sample Type '{0}.'".format(_10C)
            _data['errors'].append(msg)

        # Store the sample type to the output data
        _data['sample_type'] = {
            "title": _10C,
            "obj": sample_type
        }

        # Check for valid sample point
        sample_point = self.get_sample_point_by_name(_10D)
        if sample_point is None:
            _data['valid'] = False
            msg = "Could not find Sample Point '{0}'.".format(_10D)
            _data['errors'].append(msg)

        # Store the sample point to the output data
        _data['sample_point'] = {
            "title": _10D,
            "obj": sample_point
        }

        # Check for valid Contact
        contact = self.get_contact_by_name(client, _2E)
        if contact is None:
            _data['valid'] = False
            msg = "Could not find Contact '{0}'.".format(_2E)
            _data['errors'].append(msg)

        # Store the Contact to the output data
        _data['contact'] = {
            "title": _2E,
            "obj": contact,
        }

        #
        # Batch Handling
        #
        batch_title = _4B
        batch_obj = None
        if batch_title:
            existing_batch = [x for x in client.objectValues('Batch')
                              if x.title == batch_title]
            if existing_batch:
                batch_obj = existing_batch[0]

        batch_fields = dict(
            # <Field id(string:rw)>,
            # <Field BatchID(string:rw)>,
            BatchID=_4C,
            # <Field title(string:rw)>,
            title=_4B,
            # <Field Client(reference:rw)>,
            Client=client,
            # <Field description(text:rw)>,
            description=_4D,
            # <Field DateSampled(datetime_ng:rw)>,
            DateSampled=DateTime(_10B),
            # <Field BatchDate(datetime:rw)>,
            # <Field BatchLabels(lines:rw)>,
            # <Field ClientProjectName(string:rw)>,
            # <Field ClientBatchID(string:rw)>,
            ClientBatchID=_4E,
            # <Field Contact(reference:rw)>,
            Contact=contact,
            # <Field CCContact(reference:rw)>,
            # <Field CCEmails(lines:rw)>,
            # <Field InvoiceContact(reference:rw)>,
            # <Field ClientBatchComment(text:rw)>,
            ClientBatchComment=_6B,
            # <Field ClientPONumber(string:rw)>,
            ClientPONumber=_2F,
            # <Field ReturnSampleToClient(boolean:rw)>,
            ReturnSampleToClient=_4F,
            # <Field SampleSite(string:rw)>,
            # <Field SampleSource(string:rw)>,
            # <Field SampleType(reference:rw)>,
            # <Field SampleMatrix(reference:rw)>,
            # <Field Remarks(text:rw)>,
            # <Field InheritedObjects(reference:rw)>,
            # <Field InheritedObjectsUI(InheritedObjects:rw)>,
            # <Field constrainTypesMode(integer:rw)>,
            # <Field locallyAllowedTypes(lines:rw)>,
            # <Field immediatelyAddableTypes(lines:rw)>,
            # <Field allowDiscussion(boolean:rw)>,
            # <Field excludeFromNav(boolean:rw)>,
            # <Field nextPreviousEnabled(boolean:rw)>,
            # <Field subject(lines:rw)>,
            # <Field relatedItems(reference:rw)>,
            # <Field location(string:rw)>,
            # <Field language(string:rw)>,
            # <Field effectiveDate(datetime:rw)>,
            # <Field expirationDate(datetime:rw)>,
            # <Field creation_date(datetime:rw)>,
            # <Field modification_date(datetime:rw)>,
            # <Field creators(lines:rw)>,
            # <Field contributors(lines:rw)>,
            # <Field rights(text:rw)>,
            # <Field Analysts(lines:rw)>,
            # <Field LeadAnalyst(string:rw)>,
            # <Field Methods(reference:rw)>,
            # <Field Profile(reference:rw)>,
            # <Field NonStandardMethodInstructions(text:rw)>,
            # <Field ApprovedExceptionsToStandardPractice(text:rw)>,
            # <Field StorageLocation(reference:rw)>,
            # <Field SampleTemperature(string:rw)>,
            # <Field SampleCondition(reference:rw)>,
            # <Field Container(reference:rw)>,
            # <Field ActivitySampled(string:rw)>,
            # <Field MediaLotNr(string:rw)>,
            # <Field QCBlanksProvided(boolean:rw)>,
            # <Field MSDSorSDS(boolean:rw)>,
            # <Field SampleAndQCLotMatch(boolean:rw)>,
            # <Field ClientSampleComment(text:rw)>,
            ClientSampleComment=_6B,
            # <Field BioHazardous(boolean:rw)>,
            # <Field ExceptionalHazards(text:rw)>,
            # <Field AmountSampled(string:rw)>,
            # <Field AmountSampledMetric(string:rw)>,
            # <Field DateQADue(datetime_ng:rw)>,
            # <Field DatePublicationDue(datetime_ng:rw)>,
            # <Field DateApproved(string:rw)>,
            # <Field DateReceived(string:rw)>,
            # <Field DateAccepted(string:rw)>,
            # <Field DateReleased(string:rw)>,
            # <Field DatePrepared(string:rw)>,
            # <Field DateTested(string:rw)>,
            # <Field DatePassedQA(string:rw)>,
            # <Field DatePublished(string:rw)>,
            # <Field DateCancelled(string:rw)>,
            # <Field DateOfRetractions(lines:rw)>
        )

        # Save the Batch for the output data
        _data['batch'] = {
            "title": batch_title,
            "obj": batch_obj,
            "batch_fields": batch_fields,
        }

        # List of profile/service identifiers to search for
        _analytes = import_data.get_analytes_data()

        # Create a list of the AnalysisServices from the profiles and services
        analyses = []
        for x in _analytes:
            analyses.extend(self.resolve_analyses(x))

        # Store the Analysis to the output data
        _data['analyses'] = []
        for analysis in analyses:
            _data['analyses'].append({
                "title": analysis.Title(),
                "obj": analysis
            })



        #
        # AR Handling
        #
        _data['analysisrequests'] = []
        samples = import_data.get_sample_data()
        for n, item in enumerate(samples):

            # ClientSampleID, Amount Sampled, Metric, Remarks
            _xB, _xC, _xD, _xE = item[:4]

            sample_fields = dict(
                #  <Field id(string:rw)>,
                #  <Field description(text:rw)>,
                #  <Field SampleID(string:rw)>,
                #  <Field ClientReference(string:rw)>,
                #  <Field ClientSampleID(string:rw)>,
                ClientSampleID=_xB,
                #  <Field LinkedSample(reference:rw)>,
                #  <Field SampleType(reference:rw)>,
                SampleType=sample_type,
                #  <Field SampleTypeTitle(computed:r)>,
                #  <Field SamplePoint(reference:rw)>,
                SamplePoint=sample_point,
                #  <Field SamplePointTitle(computed:r)>,
                #  <Field SampleMatrix(reference:rw)>,
                #  <Field StorageLocation(reference:rw)>,
                #  <Field SamplingWorkflowEnabled(boolean:rw)>,
                #  <Field DateSampled(datetime:rw)>,
                DateSampled=DateTime(_10B),
                #  <Field Sampler(string:rw)>,
                #  <Field SamplingDate(datetime:rw)>,
                #  <Field PreparationWorkflow(string:rw)>,
                #  <Field SamplingDeviation(reference:rw)>,
                #  <Field SampleCondition(reference:rw)>,
                #  <Field DateReceived(datetime:rw)>,
                #  <Field ClientUID(computed:r)>,
                #  <Field SampleTypeUID(computed:r)>,
                #  <Field SamplePointUID(computed:r)>,
                #  <Field Composite(boolean:rw)>,
                #  <Field DateExpired(datetime:rw)>,
                #  <Field DisposalDate(computed:r)>,
                #  <Field DateDisposed(datetime:rw)>,
                #  <Field AdHoc(boolean:rw)>,
                #  <Field Remarks(text:rw)>,
                Remarks=_xE,
                #  <Field ClientSampleComment(text:rw)>,
                #  <Field AmountSampled(string:rw)>,
                AmountSampled=_xC,
                #  <Field AmountSampledMetric(string:rw)>,
                AmountSampledMetric=_xD,
                #  <Field ExceptionalHazards(text:rw)>,
                #  <Field SampleSite(string:rw)>,
                #  <Field ReturnSampleToClient(boolean:rw)>,
                ReturnSampleToClient=_4F,
                #  <Field Hazardous(boolean:rw)>,
                #  <Field SampleTemperature(string:rw)>
            )

            ar_fields = dict(
                # <Field id(string:rw)>,
                # <Field title(string:rw)>,
                # <Field description(text:rw)>,
                # <Field RequestID(string:rw)>,
                # <Field Client(reference:rw)>,
                Client=client,
                # <Field Contact(reference:rw)>,
                Contact=contact,
                # <Field CCContact(reference:rw)>,
                # <Field CCEmails(lines:rw)>,
                # <Field InvoiceContact(reference:rw)>,
                # <Field Sample(reference:rw)>,
                # <Field Batch(reference:rw)>,
                # <Field SubGroup(reference:rw)>,
                # <Field Template(reference:rw)>,
                # <Field Profile(reference:rw)>,
                Profile = self.profile,
                # <Field DateSampled(datetime:rw)>,
                # <Field Sampler(string:rw)>,
                # <Field SamplingDate(datetime:rw)>,
                # <Field SampleSite(string:rw)>,
                # <Field SampleType(reference:rw)>,
                # <Field SampleMatrix(reference:rw)>,
                # <Field Specification(reference:rw)>,
                # <Field ResultsRange(analysisspec:rw)>,
                # <Field PublicationSpecification(reference:rw)>,
                # <Field SamplePoint(reference:rw)>,
                # <Field StorageLocation(reference:rw)>,
                # <Field ClientOrderNumber(string:rw)>,
                # <Field ClientReference(string:rw)>,
                # <Field ClientSampleID(string:rw)>,
                # <Field SamplingDeviation(reference:rw)>,
                # <Field SampleCondition(reference:rw)>,
                # <Field DefaultContainerType(reference:rw)>,
                # <Field AdHoc(boolean:rw)>,
                # <Field Composite(boolean:rw)>,
                # <Field ReportDryMatter(boolean:rw)>,
                # <Field InvoiceExclude(boolean:rw)>,
                # <Field Analyses(analyses:rw)>,
                # <Field Attachment(reference:rw)>,
                # <Field Invoice(reference:rw)>,
                # <Field DateReceived(datetime:rw)>,
                # <Field DatePublished(datetime:rw)>,
                # <Field Remarks(text:rw)>,
                # <Field MemberDiscount(fixedpoint:rw)>,
                # <Field ClientUID(computed:r)>,
                # <Field SampleTypeTitle(computed:r)>,
                # <Field SamplePointTitle(computed:r)>,
                # <Field SampleUID(computed:r)>,
                # <Field SampleID(computed:r)>,
                # <Field ContactUID(computed:r)>,
                # <Field ProfileUID(computed:r)>,
                # <Field Invoiced(computed:r)>,
                # <Field ChildAnalysisRequest(reference:rw)>,
                # <Field ParentAnalysisRequest(reference:rw)>,
                # <Field PreparationWorkflow(string:rw)>,
                # <Field Priority(reference:rw)>,
                # <Field ResultsInterpretation(text:rw)>,
                # <Field SampleTemperature(string:rw)>,
                # <Field ReturnSampleToClient(boolean:rw)>,
                ReturnSampleToClient=_4F,
                # <Field Hazardous(boolean:rw)>,
                # <Field ClientSampleComment(text:rw)>,
                # <Field ExceptionalHazards(text:rw)>,
                # <Field NonStandardMethodInstructions(text:rw)>,
                # <Field ApprovedExceptionsToStandardPractice(text:rw)>,
                # <Field AmountSampled(string:rw)>,
                # <Field AmountSampledMetric(string:rw)>
            )

            _item = {'analyses': map(lambda an: an.UID(), analyses),
                     'sample_fields': sample_fields,
                     'ar_fields': ar_fields
                     }

            sample = self.get_sample_by_sid(client, _xB)
            if sample:
                _item['sample_obj'] = sample
                ars = sample.getAnalysisRequests()
                if ars:
                    _item['analysisrequest_obj'] = ars[0]
                else:
                    _item['analysisrequest_obj'] = None
            else:
                _item['sample_obj'] = None
                _item['analysisrequest_obj'] = None

            _data['analysisrequests'].append(_item)

        return _data

    def _import_file(self, csvfile):
        """Import the CSV file.
        """
        # get the import data
        import_data = self._prepare_import_data(csvfile)

        # Import success: switch on errors
        import_data['success'] = True

        if import_data['valid'] is False:
            import_data['success'] = False
            return import_data

        #
        # Data seems valid - importing
        #

        # Initialize the Progress Bar
        self.progressbar_init("Importing File")

        # get the client object
        client = import_data['client']['obj']

        # get the batch object
        batch = import_data['batch']['obj']
        batch_fields = import_data['batch']['batch_fields']
        if batch is None:
            # create a new batch
            batch = self.create_object("Batch", client, **batch_fields)
        batch.edit(**batch_fields)

        # Create ARs, Samples, Analyses and Sample Partitions
        ar_items = import_data['analysisrequests']
        for n, item in enumerate(ar_items):
            #
            sample = item['sample_obj']
            field_values = item['sample_fields']
            field_values.update(item['ar_fields'])
            field_values['Batch'] = batch
            field_values['Sample'] = sample

            ar = item['analysisrequest_obj']
            if ar:
                # Edit values of existing sample/AR
                ar.edit(**field_values)
                sample.edit(**field_values)
                ar.setAnalyses(item['analyses'])
            else:
                # create a new AR
                parts = [{'services': [item['analyses'], ],
                          'separate': False,
                          'container': None,
                          'preservation': None,
                          'minvol': None,
                          }]
                create_analysisrequest(
                    client, self.request, field_values,
                    analyses=item['analyses'], partitions=parts)

            # progress
            self.progressbar_progress(n, len(ar_items))

        notifyContainerModified(client)
        return import_data

    def create_object(self, content_type, container, id=None, **kwargs):
        """Create a new ARImportItem object by type
        """
        if id is None:
            id = tmpID()
        obj = _createObjectByType(content_type, container, id)
        obj.unmarkCreationFlag()
        obj.edit(**kwargs)
        obj._renameAfterCreation()
        notify(ObjectInitializedEvent(obj))
        obj.at_post_create_script()
        notify(ObjectCreatedEvent(obj))
        notify(ObjectAddedEvent(obj, container, obj.id))
        notifyContainerModified(container)
        logger.info("Created Content {0} in Container {1} with ID {2}".format(
            content_type, container, obj.id))
        return obj

    def resolve_analyses(self, value):
        """Resolve a value to a Service, or a list of services.  Value can be
        any of the following:

        - Service Title
        - Service Keyword
        - CAS NR of Analysis Service
        - Profile Title

        These are searched in order, and the first match is the winner.
        If a value can't be resolved to a service, an error is flagged

        Returns a list of service objects found.

        """
        bsc = self.bika_setup_catalog
        value = value.strip()

        # Service Title?
        brains = bsc(portal_type='AnalysisService', title=value)
        if brains:
            return [brains[0].getObject()]

        # Service Keyword?
        brains = bsc(portal_type='AnalysisService', getKeyword=value)
        if brains:
            return [brains[0].getObject()]

        # CAS nr of brains?
        clean_value = re.sub('\W', '_', value).lower()
        brains = bsc(portal_type='AnalysisService', Identifiers=clean_value)
        if brains:
            return [brains[0].getObject()]

        # Profile Title?
        brains = bsc(portal_type='AnalysisProfile', title=value)
        if brains:
            self.profile = brains[0].getObject()
            return [x for x in brains[0].getObject().getService()]

        self.statusmessage("Cannot locate service with value '{}'".format(
            value
        ))

        return []

    def get_sample_by_sid(self, client, sid):
        """Get the sample object by name
        """
        sample = [x for x in client.objectValues('Sample')
                  if x.getClientSampleID() == sid]
        if sample:
            return sample[0]
        return None

    def get_contact_by_name(self, client, name):
        """Get the contact object by name
        """
        contact = [x for x in client.objectValues('Contact')
                   if x.getFullname() == name]
        if contact:
            return contact[0]

        return None

    def get_sample_type_by_name(self, name):
        """Get the sample type object by name
        """
        results = self.bika_setup_catalog(
            dict(portal_type="SampleType", title=name))
        if results:
            return results[0].getObject()
        return None

    def get_sample_point_by_name(self, name):
        """Get the sample type object by name
        """
        results = self.bika_setup_catalog(
            dict(portal_type="SamplePoint", title=name))
        if results:
            return results[0].getObject()
        return None

    def progressbar_init(self, title):
        """Progress Bar
        """
        bar = ProgressBar(self.context, self.request, title, description='')
        notify(InitialiseProgressBar(bar))

    def progressbar_progress(self, n, total):
        """Progres Bar Progress
        """
        progress_index = float(n) / float(total) * 100.0
        progress = ProgressState(self.request, progress_index)
        notify(UpdateProgressEvent(progress))

    def get_client_by_id(self, id):
        """Search the Client by the given ID
        """
        results = self.portal_catalog(portal_type='Client', id=id)
        if results:
            return results[0].getObject()
        return None

    def statusmessage(self, msg, facility="info"):
        """Add a statusmessage to the response
        """
        return IStatusMessage(self.request).addStatusMessage(msg, facility)

    def form_get(self, key):
        """Get the value from the form
        """
        form = self.request.form
        value = form.get(key)
        logger.debug("key={0} -> value={1}".format(key, value))
        return value


class ImportData(UserDict):
    """Dictionary wrapper to hold the spreadsheet data.
    """

    # Internal data representation of the spreadsheet table.
    # Description:
    # The keys (sections) must match the values of the first column (lowered
    # and underdashified). Value of the same row get stored in fields key.
    # Following lines matching no section get appended to the data key.
    _data = {
        "header": {
            "fields": [],
            "data": [],
        },
        "batch_header": {
            "fields": [],
            "data": [],
        },
        "batch_meta": {
            "fields": [],
            "data": [],
        },
        "analytes": {
            "fields": [],
            "data": [],
        },
        "samples_meta": {
            "fields": [],
            "data": [],
        },
        "samples": {
            "fields": [],
            "data": [],
        },
    }

    def __init__(self, csvfile, delimiter=";", quotechar="'"):
        logger.info("ImportData::__init__")
        self.csvfile = csvfile
        self.csvfile.seek(0)
        self.reader = csv.reader(csvfile, delimiter=delimiter, quotechar="'")
        self.data = self.clone_data()
        self.parse()

    def clone_data(self):
        """Make a deepcopy of the data structure
        """
        import copy
        return copy.deepcopy(self._data)

    def parse(self):
        """Parse the CSV to the internal data structure
        """
        logger.info("Parsing CSV.")

        section = None
        for n, row in enumerate(self.reader):
            # we use row[0] as an identifier per row to match the key in the
            # data dict, e.g. Batch Header -> batch_header
            identifier = row[0].replace(" ", "_").lower()

            # get the row data
            row_data = self.get_row_data(row)

            # skip empty cells
            if row_data is None:
                # logger.warn("Row {0} contains no data, skipping.".format(n))
                continue

            # check if the current identifier matches a key in the data dict
            if identifier in self.data:
                # a new section begins
                section = identifier
                # remember the fields
                self.data[identifier]['fields'] = row_data
                # go to the next row
                continue

            try:
                # append the row data to the "data" key of the current section
                self.data[section]['data'].append(row_data)
            except KeyError:
                logger.error("Found invalid identifier '{}' in Line {}".format(
                    row[0], n + 1))
                # XXX: Mark the whole set as invalid or continue?
                continue
        return self.data

    def clear_data(self):
        """Clear the internal data structure
        """
        logger.info("************* CLEAR ***************")
        self.data = self.clone_data()

    def get_row_data(self, row, start=1, remove_trailing_empty=True):
        """extract the row values starting from 'start' and removes trailing
        empty values, e.g.: ['a', 'b', '', 'd', '', ''] -> ['b', '', 'd']
        """
        end = len(row)
        if remove_trailing_empty:
            # we iterate from the end of the list to the start to remove
            # empty cells
            rev = reversed(row)
            for n, i in enumerate(rev):
                if n + 1 == len(row):
                    return None
                if i != "":
                    return row[start:end - n]
        return row[start:end]

    def validate(self):
        """Validate the internal data structure
        """
        # Validate the sections
        for section in self.keys():
            logger.info("Processing Section {0}".format(section))

            fields = self.get_fields(section)
            data = self.get_data(section)

            if not fields:
                return "Invalid section {0}: No fields".format(section)
            if not data:
                return "Invalid section {0}: No data".format(section)

        # Validate the filename
        # XXX: Why do we need to do this?
        csv_filename = str(self.get_csv_filename())
        data_filename = str(self.get_data_filename())

        if csv_filename.lower() != data_filename.lower():
            return "Filename '{}' does not match entered filename '{}'".format(
                csv_filename, data_filename)

        return True

    def to_json(self):
        """Return the data as a JSON string
        """
        return json.dumps(
            self.data, indent=2, sort_keys=True, ensure_ascii=False)

    def get_csv_filename(self):
        """Return the filename of the CSV
        """
        filename = os.path.basename(self.csvfile.filename)
        return os.path.splitext(filename)[0]

    def get_data_filename(self):
        """Return the filename of the "Header" section
        """
        header = self.get_data("header")
        return header[0]

    def get_fields(self, section):
        """Fields accessor for the named section
        """
        return self.data[section]['fields']

    def get_data(self, section):
        """Data accessor for the named section
        """
        data = self.data[section]['data']
        if section == "samples":
            return data
        if len(data) == 1:
            return data[0]
        return data

    def get_sample_data(self):
        """Return the data of the "Samples" section
        """
        return self.get_data("samples")

    def get_analytes_data(self):
        """Return the data of the "Analytes" section
        """
        return self.get_data("analytes")
