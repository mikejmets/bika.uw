from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from bika.lims.browser import BrowserView
from bika.lims import bikaMessageFactory as _


class ViewView(BrowserView):
    """
    """
    template = ViewPageTemplateFile("view.pt")

    def __init__(self, context, request):
        super(ViewView, self).__init__(context, request)

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
        sampledwithmetric = schema['AmountSampled'].get(context) + ' ' + \
                            schema['AmountSampledMetric'].get(context)
        biohazardous = schema['BioHazardous'].get(context)
        qcbp = schema['QCBlanksProvided'].get(context)
        sqcm = schema['SampleAndQCLotMatch'].get(context)
        samplecondition = schema['SampleCondition'].get(context)
        datesampled = self.ulocalized_time(schema['DateSampled'].get(context))
        rows = [
            ('Client', client.Title() if client else ''),
            ('ClientProjectName', schema['ClientProjectName'].get(context)),
            ('Contact', contact.Title() if contact else ''),
            ('ClientPONumber', schema['ClientPONumber'].get(context)),
            ('LeadAnalyst', schema['LeadAnalyst'].get(context)),
            ('ReturnSampleToClient', _('Yes') if rstc else _('No')),
            ('ClientBatchID', schema['ClientBatchID'].get(context)),
            ('Profile', profile.Title() if profile else ''),
            ('ActivitySampled', schema['ActivitySampled'].get(context)),
            ('DateSampled', datesampled),
            ('SampleSource', schema['SampleSource'].get(context)),
            ('SampleSite', schema['SampleSite'].get(context)),
            ('SampleType', sampletype.Title() if sampletype else ''),
            ('MediaLotNr', schema['MediaLotNr'].get(context)),
            ('SampleMatrix', samplematrix.Title() if samplematrix else ''),
            ('SampleTemperature', schema['SampleTemperature'].get(context)),
            ('SampleCondition',
             samplecondition.Title() if samplecondition else ''),
            ('AmountSampled', sampledwithmetric),
            # ('StorageLocation', schema['StorageLocation'].get(context)),
            # ('Container', schema['Container'].get(context))),
            ('BioHazardous', _('Yes') if biohazardous else _('No')),
            ('QCBlanksProvided', _('Yes') if qcbp else _('No')),
            ('SampleAndQCLotMatch', _('Yes') if sqcm else _('No')),
            ('MSDSorSDS', schema['MSDSorSDS'].get(context))
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
        DateOfRetractions = self.ulocalized_time(DateOfRetractions,
                                                 long_format=True) \
            if DateOfRetractions else ''
        DateQADue = schema['DateQADue'].get(context)
        DateQADue = self.ulocalized_time(DateQADue, long_format=True) \
            if DateQADue else ''
        DatePublicationDue = schema['DatePublicationDue'].get(context)
        DatePublicationDue = self.ulocalized_time(DatePublicationDue,
                                                  long_format=True) \
            if DatePublicationDue else ''
        rows.extend([
            ('DateApproved', self.ulocalized_time(DateApproved)
                                                  if DateApproved else ''),
            ('DateReceived', self.ulocalized_time(DateReceived)
                                                  if DateReceived else ''),
            ('DateAccepted', self.ulocalized_time(DateAccepted)
                                                  if DateAccepted else ''),
            ('DateReleased', self.ulocalized_time(DateReleased)
                                                  if DateReleased else ''),
            ('DatePrepared', self.ulocalized_time(DatePrepared)
                                                  if DatePrepared else ''),
            ('DateTested', self.ulocalized_time(DateTested)
                                                if DateTested else ''),
            ('DatePassedQA', self.ulocalized_time(DatePassedQA)
                                                  if DatePassedQA else ''),
            ('DatePublished', self.ulocalized_time(DatePublished)
                                                   if DatePublished else ''),
            ('DateCancelled', self.ulocalized_time(DateCancelled)
                                                   if DateCancelled else ''),
            ('DateOfRetractions', DateOfRetractions),
            ('DateQADue', self.ulocalized_time(DateQADue if DateQADue else '')),
            ('DatePublicationDue', self.ulocalized_time(DatePublicationDue)
                                             if DatePublicationDue else '')
        ])

        batchlabels = ", ".join(schema['BatchLabels'].get(context))
        rows.append(('BatchLabels', batchlabels))

        if not show_empty:
            rows = [r for r in rows if r[1]]
        return rows

    def methods(self):
        """Return list of titles of associated methods.
        """
        context = self.context
        schema = context.Schema()
        methods = schema['Methods'].get(context)
        out = []
        if methods:
            for method in methods:
                out.append(method.Title())
        return out

    def __call__(self):
        return self.template()
