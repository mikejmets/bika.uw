# -*- coding: utf-8 -*-

from bika.lims.browser.arimport.handler import ImportHandler as BaseHandler
from bika.lims.interfaces import IARImportHandler
from bika.lims.utils import tmpID
from bika.lims.utils.analysisrequest import create_analysisrequest
from bika.lims.utils.sample import create_sample
from bika.lims.utils.samplepartition import create_samplepartition
from zope.interface import implements

import transaction
from DateTime import DateTime
from Products.Archetypes.event import ObjectInitializedEvent
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import _createObjectByType
from zExceptions import Redirect
from zope import event


class ImportHandler(BaseHandler):
    """Override arimport behaviour
    """
    implements(IARImportHandler)

    def __init__(self, context, request):
        super(ImportHandler, self).__init__(context, request)

    def parse_raw_data(self):
        """Parse the UW-format of import file, do some limited parsing,
        and store the values

        This is intentionally brittle, the UW form requires certain
        fields at certain positions, and is fixed.  Further modifications
        to the input file require modifications to this code.
        """

        context = self.context
        bc = getToolByName(context, 'bika_catalog')
        bsc = getToolByName(context, 'bika_setup_catalog')

        blob = context.Schema()['RawData'].get(context)
        lines = blob.data.splitlines()

        # Header data
        line = [x.strip('"').strip("'") for x in lines[1].split(',')]
        _clientname = line[2]
        _clientid = line[3]
        _contactname = line[4]
        _clientordernumber = line[5]
        _clientreference = line[6]
        # Batch data
        line = [x.strip('"').strip("'") for x in lines[3].split(',')]
        _batchtitle = line[1]
        _batchid = line[2]
        _batchdescription = line[3]
        _clientbatchid = line[4]
        returnsampletoclient = line[5]
        # "Batch meta" (just more batch data really)
        line = [x.strip('"').strip("'") for x in lines[5].split(',')]
        _clientbatchcomment = line[1]
        _labbatchcomment = line[2]
        # analytes (profile titles, service titles, service keywords, CAS nr)
        line = [x.strip('"').strip("'") for x in lines[7].split(',')]
        _analytes = [x for x in line[1:] if x]
        # Samples "meta" (common values for all samples)
        line = [x.strip('"').strip("'") for x in lines[9].split(',')]
        _datesampled = line[1]
        _sampletype = line[2]
        _samplepoint = line[3]
        _activitysampled = line[4]
        # count the number of sample rows
        nr_samples = len([x for x in lines[11:] if len(x.split(',')) > 1])

        # If batch already exists, link it now.
        brains = bc(portal_type='Batch', title=_batchtitle)
        batch = brains[0].getObject() if brains else None

        # SampleType and SamplePoint can remain strings for validator to use
        # in messages.
        brains = bsc(portal_type='SamplePoint', title=_samplepoint)
        samplepoint = brains[0].getObject() if brains else None
        brains = bsc(portal_type='SampleType', title=_sampletype)
        sampletype = brains[0].getObject() if brains else None

        # Write applicable values to ARImport schema
        # These are values that will be used in all created objects,
        # and are set only once.
        arimport_values = {
            'ClientName': _clientname,
            'ClientID': _clientid,
            'ClientOrderNumber': _clientordernumber,
            'ClientReference': _clientreference,
            'ContactName': _contactname,
            'CCContacts': [],
            'SamplePoint': samplepoint,
            'SampleType': sampletype,
            'ActivitySampled': _activitysampled,
            'BatchTitle': _batchtitle,
            'BatchDescription': _batchdescription,
            'BatchID': _batchid,
            'ClientBatchID': _clientbatchid,
            'LabBatchComment': _labbatchcomment,
            'ClientBatchComment': _clientbatchcomment,
            'Batch': batch,
            'NrSamples': nr_samples,
        }
        # Write initial values to ARImport schema
        for fieldname, fieldvalue in arimport_values.items():
            context.Schema()[fieldname].set(context, fieldvalue)

        itemdata = []
        for sample_nr in range(nr_samples):
            line = [x.strip('"').strip("'")
                    for x in lines[11 + sample_nr].split(',')]
            clientsampleid = line[1]
            amountsampled = line[2]
            metric = line[3]
            remarks = line[4]
            values = {
                'ClientSampleID': clientsampleid,
                'AmountSampled': amountsampled,
                'AmountSampledMetric': metric,
                'DateSampled': _datesampled,
                'Analyses': _analytes,
                'Remarks': remarks,
                # 'Profile': self.profile,
            }
            itemdata.append(values)
            context.Schema()['ItemData'].set(context, itemdata)
        context.reindexObject()

    def validate(self):
        """Resolve and validate stored values

        This function is responsible for setting context.Valid=True.

        If this function does not set Valid=True, the reasons why must
        be stored in context.Errors.
        """

        context = self.context
        pc = getToolByName(context, 'portal_catalog')
        bc = getToolByName(context, 'bika_catalog')

        errors = []

        # Validate Client info
        client = None
        clientname = context.Schema()['ClientName'].get(context)
        clientid = context.Schema()['ClientID'].get(context)
        brains = pc(portal_type='Client', getName=clientname)
        if brains:
            # Client name found: validate client's ID against import file
            client = brains[0].getObject()
            if clientid and clientid != client.getClientID():
                errors.append(
                    "Client '{}' has ID '{}', but you specified '{}'".format(
                        client.Title(), client.getClientID(), clientid))
        else:
            # Client name not found
            errors.append(
                "Client name is invalid; please select a valid client, "
                "or enter a valid Client Name.")
        if client:
            if context.aq_parent != client:
                # Wrong client name specified
                errors.append("Selected client '{}' should be '{}'!".format(
                    client.Title(), context.aq_parent.Title()))

        # Validate ContactName
        if client:
            contactname = context.Schema()['ContactName'].get(context)
            if not self.is_valid_contact(contactname):
                errors.append(
                    "Contact name is not a valid contact for this client.")
        else:
            errors.append(
                "Cannot validate Contact until valid Client is selected.")

        # Validate integrity of the different batch fields if the
        # Batch ID or Title reference an existing batch.
        batch = None

        batch_id = context.getBatchID()
        batch_title = context.getBatchTitle()
        # First try to find existing batch
        brains = bc(portal_type='Batch', id=batch_id)
        if not brains:
            brains = bc(portal_type='Batch', title=batch_title)
        if brains:
            batch = brains[0].getObject()
            # if both title and id are specified, make sure they both match
            if batch_title and batch_id:
                if batch.Title() != batch_title:
                    errors.append("Existing Work Order title is not {}".format(
                        batch_title
                    ))
                if batch.getId() != batch_id:
                    errors.append("Existing Work Order ID is not {}".format(
                        batch_id
                    ))

        # Simple SamplePoint validation
        sp = context.Schema()['SamplePoint'].get(context)
        if isinstance(sp, basestring):
            errors.append("'{}' is not a valid sample point.".format(sp))
        if not sp:
            errors.append(
                "The selected sample point/sampling location was not found.")

        # Simple SamplePoint validation
        st = context.Schema()['SampleType'].get(context)
        if isinstance(st, basestring):
            errors.append("'{}' is not a valid sample point.".format(st))
        if not st:
            errors.append(
                "The selected sample medium/sample type was not found.")

        # Validate ItemData fields
        for item in context.Schema()['ItemData'].get(self.context):
            csid = item['ClientSampleID']
            # Analytes
            for analyte in item['Analyses']:
                uids = self.resolve_analyses(analyte)
                if isinstance(uids, basestring):
                    errors.append("{}: {}".format(csid, uids))
            # DateSampled
            try:
                DateTime(item['DateSampled'])
            except:
                errors.append("{}: Invalid date {}".format(
                    csid, item['DateSampled']))

        context.Schema()['Errors'].set(context, errors)
        if not errors:
            context.Schema()['Valid'].set(context, True)

        valid = context.Schema()['Valid'].get(context)
        if not valid:
            self.statusmessage("There were errors during validation.")
            url = self.context.absolute_url() + "/base_edit"
            transaction.commit()
            raise Redirect(url)

    def is_valid_contact(self, fullname):
        contacts = self.context.aq_parent.objectValues('Contact')
        for contact in contacts:
            if contact.getFullname() == fullname:
                return True
        return False

    def import_items(self):

        context = self.context
        request = context.REQUEST
        uc = getToolByName(context, 'uid_catalog')
        bika_catalog = getToolByName(context, 'bika_catalog')

        client = context.aq_parent
        contact = [c for c in client.objectValues('Contact')
                   if c.getFullname() == self.context.getContactName()][0]

        self.progressbar_init('Submitting AR Import')

        # Find existing batch or create new batch if required.
        batch = None
        batch_id = context.getBatchID()
        batch_title = context.getBatchTitle()
        # First try to find existing batch
        brains = bika_catalog(portal_type='Batch', id=batch_id)
        if not brains:
            brains = bika_catalog(portal_type='Batch', title=batch_title)
        if brains:
            batch = brains[0]
        if not batch:
            # Create batch if it does not exist
            _bid = batch_id if batch_id else tmpID()
            batch = _createObjectByType("Batch", client, _bid)
            batch.unmarkCreationFlag()
            batch.edit(
                title=batch_title,
                description=context.getBatchDescription(),
                ClientBatchID=context.getClientBatchID(),
                Remarks=context.getLabBatchComment(),
                ClientBatchComment=context.getClientBatchComment()
            )
            if not batch_id:
                batch._renameAfterCreation()
            event.notify(ObjectInitializedEvent(batch))
            batch.at_post_create_script()

        itemdata = context.Schema()['ItemData'].get(context)
        for n, item in enumerate(itemdata):
            service_uids = []
            for a in item['Analyses']:
                service_uids.extend(self.resolve_analyses(a))

            # Create Sample
            sample_values = {
                'ClientReference': context.getClientReference(),
                'ClientSampleID': item['ClientSampleID'],
                'SampleType': context.getSampleType(),
                'SamplePoint': context.getSamplePoint(),
                'DateSampled': DateTime(item['DateSampled']),
                'SamplingDate': DateTime(item['DateSampled']),
                'Remarks': item['Remarks'],
            }
            sample = create_sample(client, request, sample_values)

            # Create AR
            ar_values = {
                'Sample': sample,
                'Contact': contact,
                'ClientOrderNumber': context.getClientOrderNumber(),
                'Remarks': item['Remarks'],
                'Batch': batch if batch else None,
            }
            ar = create_analysisrequest(
                client, request, ar_values, analyses=service_uids,
                partitions=[{}]
            )

            # Create and link partitions with analyses.
            part_values = {u'container': [],
                           u'minvol': u'0 ml',
                           'part_id': sample.getId() + "-P1",
                           u'preservation': [],
                           u'separate': False,
                           u'services': service_uids}
            part = create_samplepartition(
                context, part_values, ar.getAnalyses(full_objects=True))

            self.progressbar_progress(n + 1, len(itemdata))
