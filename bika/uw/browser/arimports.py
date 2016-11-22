# -*- coding: utf-8 -*-

import csv
import json
import re

from UserDict import UserDict
from bika.lims.interfaces import IARImportHandler
from bika.lims.utils import tmpID
from bika.lims.utils.analysisrequest import create_analysisrequest
from cStringIO import StringIO

import DateTime
from Products.Archetypes.event import ObjectInitializedEvent
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import _createObjectByType
from Products.statusmessages.interfaces import IStatusMessage
from bika.uw import logger
from collective.progressbar.events import InitialiseProgressBar
from collective.progressbar.events import ProgressBar
from collective.progressbar.events import ProgressState
from collective.progressbar.events import UpdateProgressEvent
from zope.container.contained import ObjectAddedEvent
from zope.container.contained import notifyContainerModified
from zope.event import notify
from zope.interface import implements
from zope.lifecycleevent import ObjectCreatedEvent


class ImportHandler:
    """Override arimport behaviour
    """
    implements(IARImportHandler)

    def __init__(self, context):
        self.context = context
        self.request = None
        self.arimport = None
        # If a batch is defined, set it here
        self.batch = None

    def __call__(self, request, arimport):
        self.request = request
        self.arimport = arimport
        return self

    def validate_data(self):
        """Prepare data for import

            - Checks data integrity
            - Extracts the known fields from the Spreadsheet
            - Maps Spreadsheet fields to Schema names
            - Fetch objects if they exist
        """

        bc = getToolByName(self.arimport, 'bika_catalog')
        client = self.arimport.aq_parent

        # get parsed_data if it exists, default value if not
        parsed_data = self.get_parsed_data()
        # empty the errors from the last parsing,
        # if more are added, the parse is flagged invalid.
        parsed_data['errors'] = []
        parsed_data['valid'] = True
        parsed_data['success'] = True

        # create dictionary from raw_data
        importdata = ImportData(self.get_raw_data())

        # Validate the import data
        valid = importdata.validate()
        if isinstance(valid, basestring):
            parsed_data['errors'].append(valid)

        # Parse the known fields from the Spreadsheet
        # Note: The variable names refer to the spreadsheet cells, e.g.:
        #       _2B is the cell at column B row 2.
        # File name, Client name, Client ID, Contact, Client Order Number,
        # Client Reference
        _2B, _2C, _2D, _2E, _2F, _2G = importdata.get_data("header")[:6]
        # title, BatchID, description, ClientBatchID, ReturnSampleToClient
        _4B, _4C, _4D, _4E, _4F = importdata.get_data("batch_header")[:5]
        # Client Comment, Lab Comment
        _6B, _6C = importdata.get_data("batch_meta")[:2]
        # DateSampled, Media, SamplePoint, Activity Sampled
        _10B, _10C, _10D, _10E = importdata.get_data("samples_meta")[:4]

        # Check for valid sample Type
        sample_type = self.get_sample_type_by_name(_10C)
        if sample_type is None:
            msg = "Could not find Sample Type '{0}.'".format(_10C)
            parsed_data['errors'].append(msg)
            parsed_data['valid'] = False
            parsed_data['success'] = False

        # Check for valid sample point
        sample_point = self.get_sample_point_by_name(_10D)
        if sample_point is None:
            msg = "Could not find Sample Point '{0}'.".format(_10D)
            parsed_data['errors'].append(msg)
            parsed_data['valid'] = False
            parsed_data['success'] = False

        # Check for valid Contact
        contact = self.get_contact_by_name(self.arimport.aq_parent, _2E)
        if contact is None:
            msg = "Could not find Contact '{0}'.".format(_2E)
            parsed_data['errors'].append(msg)
            parsed_data['valid'] = False
            parsed_data['success'] = False

        # noinspection PyBroadException
        try:
            # noinspection PyCallingNonCallable
            DateTime.DateTime(_10B)
        except:
            msg = "Could not parse date string '{}'".format(_10B)
            parsed_data['errors'].append(msg)
            parsed_data['valid'] = False
            parsed_data['success'] = False

        # Batch Handling
        existing_batch_title = _4B
        if existing_batch_title:
            brains = bc(portal_type="Batch", title=existing_batch_title)
            existing_batch_uid = brains[0].UID if brains else None
        else:
            existing_batch_uid = None
        batch_fields = {
            'uid': existing_batch_uid,
            'BatchID': _4C,
            'title': _4B,
            'Client': client.UID(),
            'description': _4D,
            'DateSampled': _10B,
            'ClientBatchID': _4E,
            'Contact': contact.UID() if contact else None,
            'ClientBatchComment': _6B,
            'ClientPONumber': _2F,
            'ReturnSampleToClient': _4F,
            'ClientSampleComment': _6B,
        }
        parsed_data['batch'] = batch_fields

        # Sample handling

        # Create a list of the AnalysisServices from the profiles and services
        analyses = []
        for x in importdata.get_analytes_data():
            resolved = self.resolve_analyses(x)
            if isinstance(resolved, basestring):
                parsed_data['errors'].append(resolved)
                parsed_data['valid'] = False
                parsed_data['success'] = False
            else:
                analyses.extend(resolved)

        # AR Handling
        parsed_data['samples'] = []
        samples = importdata.get_sample_data()
        for n, item in enumerate(samples):

            # ClientSampleID, Amount Sampled, Metric, Remarks
            _xB, _xC, _xD, _xE = item[:4]

            fields = {
                'uid': None,
                'Client': client.UID() if client else None,
                'Contact': contact.UID() if contact else None,
                'ClientSampleID': _xB,
                'SampleType': sample_type.UID(),
                'SamplePoint': sample_point.UID(),
                'DateSampled': _10B,
                'Remarks': _xE,
                'AmountSampled': _xC,
                'AmountSampledMetric': _xD,
                'ReturnSampleToClient': _4F,
                'Profile': None,
                'Analyses': map(lambda an: an.UID(), analyses),
            }

            parsed_data['samples'].append(fields)

        # Initialize the Progress Bar
        self.progressbar_init("Importing File")

        # Create required ARImportItems so that the GUI has something
        # for the GridWidgets to display
        for n, sampledata in enumerate(parsed_data['samples']):
            next_num = tmpID()
            self.progressbar_progress(n, len(parsed_data['samples']))

            if len(analyses) > 0:
                a_uids = [a.UID() for a in analyses]

                aritem_id = '%s_%s' % ('aritem', (str(next_num)))
                aritem = _createObjectByType("ARImportItem", self.arimport,
                                             aritem_id)
                aritem.edit(
                    AmountSampled=sampledata['AmountSampled'],
                    AmountSampledMetric=sampledata['AmountSampledMetric'],
                    Analyses=a_uids,
                    ClientSid=sampledata['ClientSampleID'],
                    SamplePoint=sampledata['SamplePoint'],
                    SampleType=sampledata['SampleType'],
                )

        arimport_values = {
            'FileName': self.request.get('csvfile').filename,
            'ParsedData': json.dumps(parsed_data),
            'ClientID': self.arimport.aq_parent.getClientID(),
            'ClientName': self.arimport.aq_parent.Title(),
            'NrSamples': len(parsed_data['samples']),
            'ClientOrderNumber': '',
            'ClientReference': '',
            'Contact': contact.UID() if contact else None,
            'CCContacts': [],
            'Batch': existing_batch_uid,
        }
        self.arimport.edit(**arimport_values)

    def import_data(self):
        """Import the CSV file.
        """

        print("UW import parsed data -----------")

        parsed_data = self.arimport.getParsedData().data

        # Immediate failure
        if parsed_data['valid'] is False:
            parsed_data['success'] = False
            return parsed_data

        #
        # Data seems valid - importing
        #

        # Initialize the Progress Bar
        self.progressbar_init("Importing File")

        # get the client object
        client = parsed_data['client']['obj']

        # get the batch object
        self.batch = parsed_data['batch']['obj']
        batch_fields = parsed_data['batch']['batch_fields']
        if self.batch is None:
            # create a new batch
            self.batch = self.create_object("Batch", client, **batch_fields)
        self.batch.edit(**batch_fields)

        # Create ARs, Samples, Analyses and Sample Partitions
        ar_items = parsed_data['analysisrequests']
        for n, item in enumerate(ar_items):
            #
            sample = item['sample_obj']
            field_values = item['sample_fields']
            field_values.update(item['ar_fields'])
            field_values['Batch'] = self.batch
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
        return parsed_data

    def get_parsed_data(self):
        parsed_data = self.arimport.getParsedData().data
        if not parsed_data:
            parsed_data = {
                "valid": False,
                "errors": [],
                "success": False,
            }
        return parsed_data

    def get_raw_data(self):
        raw_data = self.arimport.getRawData().data
        if not raw_data:
            raw_data = self.request.form['csvfile'].read()
            if raw_data:
                self.arimport.setRawData(raw_data)
        return raw_data

    def set_arimport_field_values(self, values):
        self.arimport.edit(**values)

    def validate_arimport(self):
        """Validation assumes the form_data has been parsed, and that
        the fields of the ARImport have been populated.

        Return true if all field values are valid.
        """

        # Parser already checks validity - there are no intermediate
        # ARImportItems to be checked in this version.
        return True

    # noinspection PyShadowingBuiltins
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
        bsc = self.arimport.bika_setup_catalog
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
            return [x for x in brains[0].getObject().getService()]

        return "Cannot locate service with value '{}'".format(value)

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
        results = self.arimport.bika_setup_catalog(
            dict(portal_type="SampleType", title=name))
        if results:
            return results[0].getObject()
        return None

    def get_sample_point_by_name(self, name):
        """Get the sample type object by name
        """
        results = self.arimport.bika_setup_catalog(
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

    # noinspection PyShadowingBuiltins
    def get_client_by_id(self, id):
        """Search the Client by the given ID
        """
        results = self.arimport.portal_catalog(portal_type='Client', id=id)
        if results:
            return results[0].getObject()
        return None

    def statusmessage(self, msg, facility="info"):
        """Add a statusmessage to the response
        """
        # noinspection PyArgumentList
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

    def __init__(self, raw_data, delimiter=";", quotechar="'", **kwargs):
        UserDict.__init__(self, **kwargs)
        logger.info("ImportData::__init__")
        stringio = StringIO(raw_data)
        self.quotechar = quotechar
        self.reader = csv.reader(stringio, delimiter=delimiter, quotechar="'")
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

        return True

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
