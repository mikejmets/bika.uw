# -*- coding: utf-8 -*-

import json

from bika.lims.browser.arimport.handler import ImportHandler as BaseHandler
from bika.lims.utils import tmpID
from bika.lims.utils.analysisrequest import create_analysisrequest

import DateTime
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import _createObjectByType
from collective.progressbar.events import InitialiseProgressBar
from collective.progressbar.events import ProgressBar
from collective.progressbar.events import ProgressState
from collective.progressbar.events import UpdateProgressEvent
from zope.container.contained import notifyContainerModified
from zope.event import notify


class ImportHandler(BaseHandler):
    """Override arimport behaviour
    """

    def validate_data(self):
        """Prepare data for import

            1) IF raw data IS NOT present in the ARImport.RawData:
                    - extract raw data from submitted form
            2) IF raw data IS present in ARImport.RawData:
               (it will be, see 1 above)
                    - extract known fields from raw data
                    - create ARImportItems for each AR to be created
                        - ARImportItem represents Sample and AR fields.
                    - check data integrity
            3) IF ARImportItem fields are validated, set ARImport.Valid = True.

            2) IF raw data IS present in ARImport.RawData
                - create ARImportItems

            - Extracts the known fields from the Spreadsheet
            - Checks data integrity
            - Creates ARImportItems
            - Flags ARImport object as valid or invalid.
        """



        bc = getToolByName(self.arimport, 'bika_catalog')
        client = self.arimport.aq_parent

        # get parsed_data if it exists, default value if not
        parsed_data = self.get_parsed_data()
        # empty the errors from the last parsing,
        # if more are added, the parse is flagged invalid.
        parsed_data['errors'] = []
        parsed_data['valid'] = True

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

        # Check for valid sample point
        sample_point = self.get_sample_point_by_name(_10D)
        if sample_point is None:
            msg = "Could not find Sample Point '{0}'.".format(_10D)
            parsed_data['errors'].append(msg)
            parsed_data['valid'] = False

        # Check for valid Contact
        contact = self.get_contact_by_name(self.arimport.aq_parent, _2E)
        if contact is None:
            msg = "Could not find Contact '{0}'.".format(_2E)
            parsed_data['errors'].append(msg)
            parsed_data['valid'] = False

        # noinspection PyBroadException
        try:
            # noinspection PyCallingNonCallable
            DateTime.DateTime(_10B)
        except:
            msg = "Could not parse date string '{}'".format(_10B)
            parsed_data['errors'].append(msg)
            parsed_data['valid'] = False

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
        # self.progressbar_init("Importing File")

        # Create required ARImportItems so that the GUI has something
        # for the GridWidgets to display
        for n, sampledata in enumerate(parsed_data['samples']):
            next_num = tmpID()
            # self.progressbar_progress(n, len(parsed_data['samples']))

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
        import pdb
        pdb.set_trace()
        pass
        self.arimport.reindexObject()

    def import_data(self):
        """Import the CSV file.
        """

        print("UW import parsed data -----------")

        parsed_data = self.arimport.getParsedData().data

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
            }
        return parsed_data

    def get_raw_data(self):
        raw_data = self.arimport.getRawData().data
        if not raw_data:
            raw_data = self.request.form['csvfile'].read()
            if raw_data:
                self.arimport.setRawData(raw_data)
        return raw_data

    def validate_arimport(self):
        """Validation assumes the form_data has been parsed, and that
        the fields of the ARImport have been populated.

        Return true if all field values are valid.
        """

        # Parser already checks validity - there are no intermediate
        # ARImportItems to be checked in this version.
        return True

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
