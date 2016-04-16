import os
import tempfile

from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from openpyxl import load_workbook
from zope.interface import implements

from bika.lims.browser import BrowserView
from bika.lims import bikaMessageFactory as _, t
from bika.lims.utils import createPdf


def a(url, text):
    return "<a href='" + url + "'>" + text + "</a>"


class ViewView(BrowserView):
    """
    """
    template = ViewPageTemplateFile("view.pt")
    pdf_wrapper = ViewPageTemplateFile("pdf_wrapper.pt")
    xlsx_upload_form = ViewPageTemplateFile("xlsx_upload_form.pt")
    view_wrapper = ViewPageTemplateFile("view_wrapper.pt")

    def __init__(self, context, request):
        BrowserView.__init__(self, context, request)
        self.context = context
        self.request = request

    def __call__(self):
        self.viewhtml = self.template()
        if self.request.form.get('pdf', False):
            self.pdf()
        elif self.request.form.get('xlsx_upload_submit', False):
            # xlsx_upload_submit must be checked before xlsx_upload
            # since xlsx_upload is in the GET request.
            return self.xlsx_upload()
        elif self.request.form.get('xlsx_upload', False):
            return self.xlsx_upload_form()
        else:
            return self.view_wrapper()

    def pdf(self):
        pdf_data = createPdf(t(self.pdf_wrapper()), css=self.css_local_fn())
        setheader = self.request.RESPONSE.setHeader
        setheader('Content-Length', len(pdf_data))
        setheader('Content-Type', 'application/pdf')
        setheader('Content-Disposition', 'inline; filename=\"%s.pdf\"' %
                  self.context.Title())
        self.request.RESPONSE.write(pdf_data)

    def xlsx_upload(self):
        xlsx_file = self.request.form.get('xlsx_file', False)
        if not xlsx_file:
            message = _("No file selected")
            self.context.plone_utils.addPortalMessage(message, 'error')
            return self.view_wrapper()
        workbook = load_workbook(filename=xlsx_file)
        


    def css_local_fn(self):
        from pkg_resources import resource_filename
        cssfn = resource_filename("bika.uw", "browser/css/batch-pdf.css")
        return cssfn

    def summary_rows(self, show_empty=True):
        """These are the pairs of fields which will be rendered in the
        summary table on the top of the Batch View.

        This output decides the ordering of fields and the html that's used
        to display them.

        html is rendered structurally in both labels and values.
        """
        context = self.context
        schema = context.Schema()
        #
        client = context.getClient()
        contact = schema['Contact'].get(context)
        rstc = schema['ReturnSampleToClient'].get(context)
        profile = schema['Profile'].get(context)
        sampletype = schema['SampleType'].get(context)
        samplematrix = schema['SampleMatrix'].get(context)
        sampledwithmetric = '%s %s' % (
            schema['AmountSampled'].get(self.context),
            schema['AmountSampledMetric'].get(self.context))
        biohazardous = schema['BioHazardous'].get(context)
        qcbp = schema['QCBlanksProvided'].get(context)
        sqcm = schema['SampleAndQCLotMatch'].get(context)
        scond = schema['SampleCondition'].get(context)
        datesampled = self.ulocalized_time(schema['DateSampled'].get(context))
        msdsorsds = schema['MSDSorSDS'].get(context)

        rows = [
            (_('Batch'), context.getId()),
            (_('Client'), client.Title() if client else ''),
            (
                _('Client Project Name'),
                schema['ClientProjectName'].get(context)),
            (_('Contact'), contact.Title() if contact else ''),
            (_('Client PO Number'), schema['ClientPONumber'].get(context)),
            (_('Lead Analyst'), schema['LeadAnalyst'].get(context)),
            (_('Return Sample To Client'), _('Yes') if rstc else _('No')),
            (_('Client BatchID'), schema['ClientBatchID'].get(context)),
            (_('Profile'), profile.Title() if profile else ''),
            (_('Activity Sampled'), schema['ActivitySampled'].get(context)),
            (_('Date Sampled'), datesampled),
            (_('Sample Source'), schema['SampleSource'].get(context)),
            (_('Sample Site'), schema['SampleSite'].get(context)),
            (_('Sample Type'), sampletype.Title() if sampletype else ''),
            (_('Media Lot Nr'), schema['MediaLotNr'].get(context)),
            (_('Sample Matrix'), samplematrix.Title() if samplematrix else ''),
            (_('Sample Temperature'), schema['SampleTemperature'].get(context)),
            (_('Sample Condition'), scond.Title() if scond else ''),
            (_('Amount Sampled'), sampledwithmetric),
            (_('Bio Hazardous'), _('Yes') if biohazardous else _('No')),
            (_('QC Blanks Provided'), _('Yes') if qcbp else _('No')),
            (_('Sample And QC Lot Match'), _('Yes') if sqcm else _('No')),
            (_('MSDS or SDS'), _('Yes') if msdsorsds else _('No'))
            # ('StorageLocation', schema['StorageLocation'].get(context)),
            # ('Container', schema['Container'].get(context))),
        ]

        DateApproved = schema['DateApproved'].get(context)
        DateApproved = self.ulocalized_time(DateApproved, long_format=True) \
            if DateApproved else ''
        DateReceived = schema['DateReceived'].get(context)
        DateReceived = self.ulocalized_time(DateReceived, long_format=True) \
            if DateReceived else ''
        DateAccepted = schema['DateAccepted'].get(context)
        DateAccepted = self.ulocalized_time(DateAccepted, long_format=True) \
            if DateAccepted else ''
        DateReleased = schema['DateReleased'].get(context)
        DateReleased = self.ulocalized_time(DateReleased, long_format=True) \
            if DateReleased else ''
        DatePrepared = schema['DatePrepared'].get(context)
        DatePrepared = self.ulocalized_time(DatePrepared, long_format=True) \
            if DatePrepared else ''
        DateTested = schema['DateTested'].get(context)
        DateTested = self.ulocalized_time(DateTested, long_format=True) \
            if DateTested else ''
        DatePassedQA = schema['DatePassedQA'].get(context)
        DatePassedQA = self.ulocalized_time(DatePassedQA, long_format=True) \
            if DatePassedQA else ''
        DatePublished = schema['DatePublished'].get(context)
        DatePublished = self.ulocalized_time(DatePublished, long_format=True) \
            if DatePublished else ''
        DateCancelled = schema['DateCancelled'].get(context)
        DateCancelled = self.ulocalized_time(DateCancelled, long_format=True) \
            if DateCancelled else ''
        DateOfRetractions = schema['DateOfRetractions'].get(context)
        DateQADue = schema['DateQADue'].get(context)
        DateQADue = self.ulocalized_time(DateQADue, long_format=True) \
            if DateQADue else ''
        DatePublicationDue = schema['DatePublicationDue'].get(context)
        DatePublicationDue = self.ulocalized_time(DatePublicationDue,
                                                  long_format=True) \
            if DatePublicationDue else ''
        rows.extend([
            (_('Date Approved'), DateApproved),
            (_('Date Received'), DateReceived),
            (_('Date Accepted'), DateAccepted),
            (_('Date Released'), DateReleased),
            (_('Date Prepared'), DatePrepared),
            (_('Date Tested'), DateTested),
            (_('Date Passed QA'), DatePassedQA),
            (_('Date Published'), DatePublished),
            (_('Date Cancelled'), DateCancelled),
            (_('Date Of Retractions'), DateOfRetractions),
            (_('Date QA Due'), DateQADue),
            (_('Date Publication Due'), DatePublicationDue),
        ])

        if not show_empty:
            rows = [r for r in rows if r[1]]

        return rows

    def detail_rows(self, show_empty=True):
        """These are the pairs of fields which are displayed with
        full-width (80%) field values (one per row).  Remarks, etc.

        This output decides the ordering of fields and the html that's used
        to display them.

        html is rendered structurally in both labels and values.
        """
        context = self.context
        schema = context.Schema()
        uc = getToolByName(context, "uid_catalog")
        #
        batchlabels = []
        for bl in schema['BatchLabels'].get(context):
            if isinstance(bl, basestring):
                batchlabels.append(uc(UID=bl)[0].Title)
            elif hasattr(bl, 'portal_type') and bl.portal_type == 'BatchLabel':
                batchlabels.append(bl.Title())
        BatchLabels = "<br/>".join(batchlabels)
        Methods = "<br/>".join(
            [x.Title() for x in schema['Methods'].get(context)])
        NonStandardMethodInstructions = schema[
            'NonStandardMethodInstructions'].get(context)
        ApprovedExceptionsToStandardPractice = schema[
            'ApprovedExceptionsToStandardPractice'].get(context)
        ExceptionalHazards = schema['ExceptionalHazards'].get(context)
        ClientBatchComment = schema['ClientBatchComment'].get(context)
        ClientSampleComment = schema['ClientSampleComment'].get(context)
        remark_items = [r for r in schema['Remarks'].get(context).split('===')
                        if r]
        Remarks = ''.join(['=== %s<br/>'%(r) for r in remark_items])
        schema['Remarks'].get(context).split()

        rows = [
            (_('Batch Labels'), BatchLabels),
            (_('Methods'), Methods),
            (_('Non Standard Method Instructions'),
             NonStandardMethodInstructions),
            (_('Approved Exceptions To Standard Practice'),
             ApprovedExceptionsToStandardPractice),
            (_('Exceptional Hazards'), ExceptionalHazards),
            (_('Client Batch Comment'), ClientBatchComment),
            (_('Client Sample Comment'), ClientSampleComment),
            (_('Remarks'), Remarks),
        ]

        if not show_empty:
            rows = [r for r in rows if r[1]]

        return rows

    def sample_pairs(self, sample):
        """Return the list of pairs for a single Sample.
        This output decides the ordering of fields and the html that's used
        to display them.  html is rendered structurally in values.
        """
        schema = sample.Schema()
        workflow = getToolByName(sample, 'portal_workflow')
        #
        sampletype = schema['SampleType'].get(sample)
        samplematrix = schema['SampleMatrix'].get(sample)
        biohazardous = schema['BioHazardous'].get(sample)
        datesampled = self.ulocalized_time(schema['DateSampled'].get(sample))
        sampledwithmetric = schema['AmountSampled'].get(sample) + ' ' + \
                            schema['AmountSampledMetric'].get(sample)
        rows = [
            (_('Sample ID'),
             a(sample.absolute_url(), sample.Title()) if sample else ''),
            (_('Client ID'),
             a(sample.absolute_url(),
               sample.getClientSampleID()) if sample else ''),
            (_('Barcode'), sample.id),
             (_('Analysis Requests'),
             ", ".join([a(ar.absolute_url(), ar.Title())
                        for ar in sample.getAnalysisRequests()])),
            (_('Sample Site'), schema['SampleSite'].get(sample)),
            (_('Sample Type'), sampletype.Title() if sampletype else ''),
            (_('Sample Matrix'), samplematrix.Title() if samplematrix else ''),
            (_('Amount Sampled'), sampledwithmetric),
            (_('Bio Hazardous'), _('Yes') if biohazardous else _('No')),
        ]
        return rows

    def sample_rows(self):
        """Return one list of key,value pairs for all samples referenced by
        this batch.
        """
        context = self.context
        schema = context.Schema()
        #  getAnalysisRequests uses backreferences on AnalysisRequestBatch:
        # so ARs are actual objects, but there could be other criteria.
        ars = context.getAnalysisRequests()
        pairs = [self.sample_pairs(sample) for sample in
                 # May be duplicate Samples (multiple ARs):
                 sorted(list(set([ar.getSample() for ar in ars])),
                        cmp=lambda x, y: cmp(x.Title(), y.Title()))
                 ]
        return pairs

    def analysis_pairs(self, analysis):
        """Return the list of pairs for a single Sample.
        This output decides the ordering of fields and the html that's used
        to display them.  html is rendered structurally in values.
        """
        ar = analysis.aq_parent
        ar_schema = ar.Schema()
        sample = ar.getSample()
        sample_schema = sample.Schema()
        #
        workflow = getToolByName(sample, 'portal_workflow')
        #
        sampledwithmetric = '%s %s' % (
            sample_schema['AmountSampled'].get(self.context),
            sample_schema['AmountSampledMetric'].get(self.context))
        #
        pairs = [
            (_('Sample ID'),
             sample.Title() if sample else ''),
            (_('Client Sample ID'),
             a(sample.absolute_url(), sample.getClientSampleID()) if sample else ''),
            (_('Analysis'),
             analysis.Title()),
        ]
        return pairs

    def analysis_rows(self):
        """Return one list of key,value pairs for all analyses! referenced
        by this batch.
        """
        context = self.context
        ars = context.getAnalysisRequests()
        analyses = []
        for ar in ars:
            analyses.extend(ar.getAnalyses(cancellation_state='active',
                                           full_objects=True))
        return [self.analysis_pairs(analysis) for analysis in analyses]
