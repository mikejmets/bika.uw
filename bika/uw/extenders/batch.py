from bika.lims import bikaMessageFactory as _

from archetypes.schemaextender.interfaces import IOrderableSchemaExtender
from archetypes.schemaextender.interfaces import ISchemaModifier
from bika.lims.browser.widgets import DateTimeWidget
from bika.lims.fields import *
from bika.lims.interfaces import IBatch
from Products.Archetypes.public import *
from zope.component import adapts

from bika.lims.browser.widgets import ReferenceWidget

DateApproved = ExtStringField(
    'DateApproved',
    schemata="Dates",
    readonly=True,
    widget=ComputedWidget(
        label=_('Date Approved'),
        description=_('The date the WOrk Order was approved.'),
        visible={'view': 'visible',
                 'edit': 'visible'}
    )
)


DateAccepted = ExtStringField(
    'DateAccepted',
    schemata="Dates",
    readonly=True,
    widget=ComputedWidget(
        label=_('Date Accepted'),
        description=_('The date the Work Order was accepted.')
    )
)

DatePrepared = ExtStringField(
    'DatePrepared',
    schemata="Dates",
    readonly=True,
    widget=ComputedWidget(
        label=_('Date Prepared'),
        description=_("The date this Work Order was prepared.")
    )
)

DateReleased = ExtStringField(
    'DateReleased',
    schemata="Dates",
    readonly=True,
    widget=ComputedWidget(
        label=_('Date Released'),
        description=_('Work Order released.')
    )
)

DateReceived = ExtStringField(
    'DateReceived',
    schemata="Dates",
    readonly=True,
    widget=ComputedWidget(
        label=_('Date Received'),
        description=_('Shows when the Work Order was received.')
    )
)

DateTested = ExtStringField(
    'DateTested',
    schemata="Dates",
    readonly=True,
    widget=ComputedWidget(
        label=_('Date Tested'),
        description=_("The date this Work Order was flagged tested.")
    )
)

DatePassedQA = ExtStringField(
    'DatePassedQA',
    schemata="Dates",
    readonly=True,
    widget=ComputedWidget(
        label=_('Date Passed QA'),
        description=_('The Work Order QA Passed.')
    )
)

DatePublished = ExtStringField(
    'DatePublished',
    schemata="Dates",
    widget=ComputedWidget(
        label=_('Date Published'),
        description=_('The Work Order last last published.')
    )
)

DateCancelled = ExtStringField(
    'DateCancelled',
    schemata="Dates",
    widget=ComputedWidget(
        label=_('Date Cancelled'),
        description=_('Contains a date, if the Work Order has been cancelled.')
    )
)

DateOfRetractions = ExtLinesField(
    'DateOfRetractions',
    schemata="Dates",
    widget=ComputedWidget(
        label=_('Date Of AR Retractions'),
        description=_('Show retraction dates for all ARs inside this Work Order.')
    )
)

DateQADue = ExtDateTimeField(
    'DateQADue',
    schemata="Dates",
    widget=DateTimeWidget(
        label=_('Date QA Due'),
        description=_("Date when QA should be due"))
)

DatePublicationDue = ExtDateTimeField(
    'DatePublicationDue',
    schemata="Dates",
    widget=DateTimeWidget(
        label=_('Date Publications Due'),
        description=_("Date when Publication should be due"))
)

DateOfExpiry = ExtStringField(
    'DateOfExpiry',
    schemata="Dates",
    readonly=True,
    widget=DateTimeWidget(
        label=_('Date Of Expiry'),
        description=_("Expiry date of samples in this Work Order")
    )
)

DateDisposed = ExtStringField(
    'DateDisposed',
    schemata="Dates",
    readonly=True,
    widget=ComputedWidget(
        label=_('Date Of Disposal (or return to client)'),
        description=_("Disposal date of samples in this Work Order")
    )
)


ActivitySampled = ExtStringField(
    'ActivitySampled',
    required=False,
    # This is not true, but required to legitimise the schemata.
    schemata="Create and Approve",
    widget=StringWidget(
        label=_('Activity Sampled'),
        visible={'view': 'visible',
                 'edit': 'visible'}
    ),
)

QCBlanksProvided = ExtBooleanField(
    'QCBlanksProvided',
    required=False,
    schemata="Assign",
    # This is not true, but required to legitimise the schemata.
    widget=BooleanWidget(
        label=_('QC Blanks Provided'),
        visible={'view': 'visible',
                 'edit': 'visible'}
    ),
)

MediaLotNr = ExtStringField(
    'MediaLotNr',
    required=False,
    schemata="Receive and Accept",
    # This is not true, but required to legitimise the schemata.
    widget=StringWidget(
        label=_('Media Lot Number'),
        visible={'view': 'visible',
                 'edit': 'visible'}
    ),
)

SampleAndQCLotMatch = ExtBooleanField(
    'SampleAndQCLotMatch',
    required=False,
    schemata="AnalysisRequest and Sample Fields",
    widget=BooleanWidget(
        label=_('Lot for samples matches QC Blanks'),
        visible={'view': 'visible',
                 'edit': 'visible'}
    ),
)

MSDSorSDS = ExtBooleanField(
    'MSDSorSDS',
    required=False,
    schemata="AnalysisRequest and Sample Fields",
    widget=BooleanWidget(
        label=_('MSDS or SDS provided'),
        visible={'view': 'visible',
                 'edit': 'visible'}
    ),
)

ClientSampleComment = ExtTextField(
    'ClientSampleComment',
    default_content_type='text/x-web-intelligent',
    allowable_content_types=('text/plain', ),
    default_output_type="text/plain",
    schemata="AnalysisRequest and Sample Fields",
    widget=TextAreaWidget(
        label=_('Client Sample Comment'),
        description=_(
            "These comments will be applied as defaults in Client Remarks field for new Samples."),
    )
)

ExceptionalHazards = ExtTextField(
    'ExceptionalHazards',
    default_content_type='text/x-web-intelligent',
    allowable_content_types=('text/plain', ),
    default_output_type="text/plain",
    schemata="Hazards",
    widget=TextAreaWidget(
        label=_('Exceptional hazards'),
        description=_(
            "The value selected here will be set as the default for new Samples."),
    )
)

AmountSampled = ExtStringField(
    'AmountSampled',
    required=False,
    schemata="Work Order Instructions",
    widget=StringWidget(
        label=_('Amount Sampled'),
        visible={'view': 'visible',
                 'edit': 'visible'}
    ),
)
AmountSampledMetric = ExtStringField(
    'AmountSampledMetric',
    required=False,
    schemata="Work Order Instructions",
    widget=StringWidget(
        label=_('Amount Sampled Metric'),
        visible={'view': 'visible',
                 'edit': 'visible'}
    ),
)

ApprovedExceptionsToStandardPractice = ExtTextField(
    'ApprovedExceptionsToStandardPractice',
    required=False,
    schemata="Work Order Instructions",
    widget=TextAreaWidget(
        label=_('Approved Exceptions To Standard Practice'),
        visible={'view': 'visible',
                 'edit': 'visible'}
    ),
)

NonStandardMethodInstructions = ExtTextField(
    'NonStandardMethodInstructions',
    required=False,
    schemata="Work Order Instructions",
    widget=TextAreaWidget(
        label=_('Non-standard Method Instructions'),
        visible={'view': 'visible',
                 'edit': 'visible'}
    ),
)


class BatchSchemaExtender(object):
    adapts(IBatch)
    implements(IOrderableSchemaExtender)

    fields = [
        ActivitySampled,
        AmountSampled,
        AmountSampledMetric,
        MediaLotNr,
        QCBlanksProvided,
        SampleAndQCLotMatch,
        MSDSorSDS,
        ClientSampleComment,
        ExceptionalHazards,
        NonStandardMethodInstructions,
        ApprovedExceptionsToStandardPractice,

        DateApproved,
        DateAccepted,
        DatePrepared,
        DateReleased,
        DateReceived,
        DateTested,
        DateQADue,
        DatePublicationDue,
        DateOfExpiry,
        DateDisposed,

        DatePassedQA,
        DatePublished,
        DateCancelled,
        DateOfRetractions,

    ]

    def __init__(self, context):
        self.context = context

    def getOrder(self, schematas):
        """Return modified order of field schematas.
        """

        schematas["Create and Approve"] = [
            "title",
            "description",
            "BatchDate",
            "BatchLabels",
            "ClientProjectName",        ## These are visible by default,
            "ClientBatchID",            ## and hidden in non-Client batches
            "Contact",                  ##
            "CCContact",                ##
            "CCEmails",                 ##
            "InvoiceContact",           ##
            "ClientBatchComment",       ##
            "ClientOrderNumber",        ##
            "ClientReference",          ##
            "ReturnSampleToClient",     ##
            "Priority",
            "SamplingDate",
            "SampleType",
            "SampleMatrix",
            "PreparationWorkflow",
            "Remarks",
            "InheritedObjects",
            "InheritedObjectsUI",
        ]
        schematas["Receive and Accept"] = [
            "SamplePoint",
            "StorageLocation",
            ## "ReturnSampleToClient",
            "SampleTemperature",
            "SampleCondition",
            "SamplingDeviation",
            ## "SampleType",
            ## "SampleMatrix",
            "DefaultContainerType",
            ## "SamplingDate",
            "DateSampled",
            "Sampler",
            "ActivitySampled",
            "MediaLotNr",
            "QCBlanksProvided",
            "MSDSorSDS",
            "SampleAndQCLotMatch",
            "ClientSampleComment",
            "BioHazardous",
            "ExceptionalHazards",
            "AmountSampled",
            "AmountSampledMetric",
        ]
        schematas["Assign"] = [
            "Analysts",
            "LeadAnalyst",
            "Specification",
            "Methods",
            "Instruments",
            "Profile",
            "NonStandardMethodInstructions",
            "ApprovedExceptionsToStandardPractice",
        ]
        schematas["Dates"] = [
            ## "BatchDate",
            "DateApproved",
            "SamplingDate",
            ## "DateSampled",
            "DateReceived",
            "DateAccepted",
            "DateReleased",
            "DatePrepared",
            "DateTested",
            "DateQADue",
            "DatePassedQA",
            "DatePublicationDue",
            "DatePublished",
            "DateOfExpiry",
            "DateDisposed",
            "DateCancelled",
            "DateOfRetractions",
        ]

        return schematas


    def getFields(self):
        return self.fields


class BatchSchemaModifier(object):
    adapts(IBatch)
    implements(ISchemaModifier)

    def __init__(self, context):
        self.context = context

    def fiddle(self, schema):
        """
        """

        # Hide fields UW doesn't care to see
        for fn in ["ARTemplate", ]:
            if fn in schema:
                schema[fn].widget.visible = {"view": "invisible",
                                             "edit": "invisible"}

        # Force-show fields that UW does want to see
        for fn in ["Priority", ]:
            if fn in schema:
                schema[fn].widget.visible = {"view": "visible",
                                             "edit": "visible"}

        # All Client Contact fields must be restricted to show only relevant
        # Contacts.
        client = self.context.getClient()
        if client:
            ids = [c.getId() for c in client.objectValues('Contact')]
            for fn in ["Contact", "CCContact", "InvoiceContact"]:
                if fn in schema:
                    schema[fn].widget.base_query['id'] = ids

        return schema
