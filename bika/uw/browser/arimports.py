# -*- coding: utf-8 -*-

import os
import csv
import types
import json
from urlparse import urljoin
from UserDict import UserDict

from DateTime import DateTime

from zope.event import notify
from zope.interface import implements

from plone.app.layout.globals.interfaces import IViewView
from plone.protect import CheckAuthenticator

from collective.progressbar.events import ProgressBar
from collective.progressbar.events import ProgressState
from collective.progressbar.events import UpdateProgressEvent
from collective.progressbar.events import InitialiseProgressBar

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.Archetypes.event import ObjectInitializedEvent
from Products.statusmessages.interfaces import IStatusMessage
from Products.CMFPlone.utils import transaction_note
from Products.CMFPlone.utils import _createObjectByType

from bika.lims.utils import tmpID
from bika.lims.browser import BrowserView
from bika.lims import bikaMessageFactory as _

from bika.uw import logger


class ClientARImportAddView(BrowserView):
    implements(IViewView)
    template = ViewPageTemplateFile('templates/arimport_add_form.pt')

    def __init__(self, context, request):
        super(ClientARImportAddView, self).__init__(context, request)
        self.context = context
        self.request = request

    def __call__(self):
        CheckAuthenticator(self.request.form)

        if self.form_get('submitted'):
            csvfile = self.form_get('csvfile')
            debug_mode = self.form_get('debug')

            if debug_mode == "1":
                return self.template()

            obj, msg = self._import_file(csvfile)
            if obj:
                msg = "Import complete"
                self.statusmessage(_(msg), "info")
                url = obj.absolute_url()
            else:
                self.statusmessage(_(msg), "error")
                url = urljoin(self.context.absolute_url(), "arimport_add")
            return self.redirect(url)

        return self.template()

    def parsed_import_data(self):
        """Return the parsed data as JSON
        """
        csvfile = self.form_get('csvfile')
        if csvfile:
            import_data = ImportData(csvfile)
            return import_data.to_json()
        return None

    def redirect(self, url):
        """Write a redirect JavaScript to the given URL
        """
        self.request.response.write("<script>document.location.href='{0}'</script>".format(url))

    def _import_file(self, csvfile):
        """Import the CSV file.
        """
        # Initialize the Progress Bar
        self.progressbar_init("Importing File")

        # parse the CSV data into the interanl data structure
        import_data = ImportData(csvfile)

        # Validate the import data
        valid = import_data.validate()
        if type(valid) in types.StringTypes:
            transaction_note(valid)
            return None, valid

        # XXX: Why do we have to do this?
        #      Are we not always in a client folder
        client_id = self.form_get("ClientID")
        client = self.get_client_by_id(client_id)
        if client is None:
            # This is not a user input issue - client_id is added to template
            return None, "Could not find Client {0}".format(client_id)

        # Note: The variable names refer to the spreadsheet cells, e.g.:
        #       _2B is the cell at column B row 2.
        #
        # File name, Client name, Client ID, Contact, Client Order Number, Client Reference
        _2B, _2C, _2D, _2E, _2F, _2G = import_data.get_data("header")
        # title, BatchID, description, ClientBatchID, ReturnSampleToClient
        _4B, _4C, _4D, _4E, _4F = import_data.get_data("batch_header")
        # Client Comment, Lab Comment
        _6B, _6C = import_data.get_data("batch_meta")
        # DateSampled, Media, SamplePoint, Activity Sampled
        _10B, _10C, _10D, _10E = import_data.get_data("samples_meta")

        batch_data = dict(
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
            # <Field Contact(reference:rw)>,
            # <Field CCContact(reference:rw)>,
            # <Field CCEmails(lines:rw)>,
            # <Field InvoiceContact(reference:rw)>,
            # <Field ClientBatchComment(text:rw)>,
            # <Field ClientPONumber(string:rw)>,
            # <Field ReturnSampleToClient(boolean:rw)>,
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

        # Create a Batch Object
        batch = self.create_object("Batch", folder=client, **batch_data)

        # List of sample data rows (lists)
        sample_data = import_data.get_sample_data()

        for n, sample in enumerate(sample_data):

            # ClientSampleID, Amount Sampled, Metric, Remarks
            _xB, _xC, _xD, _xE = sample

            # sample = self.create_object("Sample", folder=client)

            # progress
            self.progressbar_progress(n, len(sample_data))

        return batch, "Success"

    def create_object(self, content_type, folder=None, id=None, **kwargs):
        """Create a new ARImportItem object by type
        """
        if id is None:
            id = tmpID()
        obj = _createObjectByType(content_type, folder, id)
        obj.processForm()
        obj.edit(**kwargs)
        obj._renameAfterCreation()
        notify(ObjectInitializedEvent(obj))
        obj.at_post_create_script()
        return obj

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

            # get the row data (column 1 to the end of the line per default)
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
                self.data[identifier]["fields"] = row_data
                # go to the next row
                continue

            try:
                # append the row data to the "data" key of the current section
                self.data[section]["data"].append(row_data)
            except KeyError:
                logger.error("Found invalid identifier '{0}' in Line {1}".format(row[0], n + 1))
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
            return "Filename '{0}' does not match entered filename '{1}'".format(
                csv_filename, data_filename)

        return True

    def to_json(self):
        """Return the data as a JSON string
        """
        return json.dumps(self.data, indent=2, sort_keys=True)

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
        return self.data[section]["fields"]

    def get_data(self, section):
        """Data accessor for the named section
        """
        data = self.data[section]["data"]
        if len(data) == 1:
            return data[0]
        return data

    def get_sample_data(self):
        """Return the data of the "Samples" section
        """
        return self.get_data("samples")
