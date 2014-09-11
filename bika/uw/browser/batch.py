from archetypes.schemaextender.interfaces import IOrderableSchemaExtender
from archetypes.schemaextender.interfaces import ISchemaModifier
from bika.lims import bikaMessageFactory as _
from bika.lims.browser.widgets import DateTimeWidget
from bika.lims.browser.widgets import DecimalWidget as bikaDecimalWidget
from bika.lims.fields import *
from bika.lims.interfaces import IBatch
from Products.Archetypes.public import *
from zope.component import adapts
from zope.interface import implements

ActivitySampled = ExtStringField(
    'ActivitySampled',
    required=False,
    schemata = "AnalysisRequest and Sample Fields",
    widget=StringWidget(
        label=_('Activity Sampled'),
        visible={'view': 'visible',
                 'edit': 'visible'}
    ),
)

QCBlanksProvided = ExtBooleanField(
    'QCBlanksProvided',
    required=False,
    schemata = "AnalysisRequest and Sample Fields",
    widget=BooleanWidget(
        label=_('QC Blanks Provided'),
        visible={'view': 'visible',
                 'edit': 'visible'}
    ),
)

MediaLotNr = ExtStringField(
    'MediaLotNr',
    required=False,
    schemata = "AnalysisRequest and Sample Fields",
    widget=StringWidget(
        label=_('Media Lot Number'),
        visible={'view': 'visible',
                 'edit': 'visible'}
    ),
)

SampleAndQCLotMatch = ExtBooleanField(
    'SampleAndQCLotMatch',
    required=False,
    schemata = "AnalysisRequest and Sample Fields",
    widget=BooleanWidget(
        label=_('Lot for samples matches QC Blanks'),
        visible={'view': 'visible',
                 'edit': 'visible'}
    ),
)

MSDSorSDS = ExtBooleanField(
    'MSDSorSDS',
    required=False,
    schemata = "AnalysisRequest and Sample Fields",
    widget=BooleanWidget(
        label=_('MSDS or SDS provided'),
        visible={'view': 'visible',
                 'edit': 'visible'}
    ),
)

ClientSampleComment = ExtTextField(
    'ClientSampleComment',
    default_content_type='text/x-web-intelligent',
    allowable_content_types = ('text/plain', ),
    default_output_type="text/plain",
    schemata = "AnalysisRequest and Sample Fields",
    widget=TextAreaWidget(
        label=_('Client Sample Comment'),
        description=_("These comments will be applied as defaults in Client Remarks field for new Samples."),
    )
)

ExceptionalHazards = ExtTextField(
    'ExceptionalHazards',
    default_content_type='text/x-web-intelligent',
    allowable_content_types = ('text/plain', ),
    default_output_type="text/plain",
    schemata = "Hazards",
    widget=TextAreaWidget(
        label=_('Exceptional hazards'),
        description=_("The value selected here will be set as the default for new Samples."),
    )
)

AmountSampled = ExtStringField(
    'AmountSampled',
    required=False,
    schemata = "Work Order Instructions",
    widget=StringWidget(
        label=_('Amount Sampled'),
        visible={'view': 'visible',
                 'edit': 'visible'}
    ),
)
AmountSampledMetric = ExtStringField(
    'AmountSampledMetric',
    required=False,
    schemata = "Work Order Instructions",
    widget=StringWidget(
        label=_('Amount Sampled Metric'),
        visible={'view': 'visible',
                 'edit': 'visible'}
    ),
)

ApprovedExceptionsToStandardPractice = ExtTextField(
    'ApprovedExceptionsToStandardPractice',
    required=False,
    schemata = "Work Order Instructions",
    widget=TextAreaWidget(
        label=_('Approved Exceptions To Standard Practice'),
        visible={'view': 'visible',
                 'edit': 'visible'}
    ),
)

NonStandardMethodInstructions = ExtTextField(
    'NonStandardMethodInstructions',
    required=False,
    schemata = "Work Order Instructions",
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
        # Default tab
        ActivitySampled,
        # ar and samples tab
        AmountSampled,
        AmountSampledMetric,
        MediaLotNr,
        QCBlanksProvided,
        SampleAndQCLotMatch,
        MSDSorSDS,
        ClientSampleComment,
        ExceptionalHazards,
        NonStandardMethodInstructions
    ]

    def __init__(self, context):
        self.context = context

    def getOrder(self, schematas):
        fields = schematas['default']
        fields.insert(fields.index('ClientProjectName') + 1,    'ActivitySampled')

        fields = schematas['AnalysisRequest and Sample Fields']
        fields.insert(fields.index('ReturnSampleToClient') + 1, 'QCBlanksProvided')
        fields.insert(fields.index('SamplePoint') + 1, 'MSDSorSDS')
        fields.insert(fields.index('SamplePoint') + 1, 'SampleAndQCLotMatch')
        fields.insert(fields.index('SamplePoint') + 1, 'MediaLotNr')
        fields.insert(fields.index('SampleTemperature') + 1, 'ClientSampleComment')

        # Move some fields into Work Order Instructions schemata
        fields = schematas['default']
        for x in ['Specification', 'ARTemplate', 'Profile', 'BioHazardous']:
            if x in fields:
                fields.remove(x)

        fields = schematas['Work Order Instructions']
        fields.insert(fields.index('NonStandardMethodInstructions')+1, 'NonStandardMethodInstructions')
        fields.insert(fields.index('NonStandardMethodInstructions')+1, 'Profile')
        fields.insert(fields.index('NonStandardMethodInstructions')+1, 'Template')
        fields.insert(fields.index('NonStandardMethodInstructions')+1, 'Instruments')
        fields.insert(fields.index('NonStandardMethodInstructions')+1, 'Methods')
        fields.insert(fields.index('NonStandardMethodInstructions')+1, 'Specification')

        fields = schematas['Hazards']
        fields.insert(fields.index('ExceptionalHazards'), 'BioHazardous')

        return schematas

    def getFields(self):
        return self.fields



class BatchSchemaModifier(object):
    adapts(IBatch)
    implements(ISchemaModifier)

    def __init__(self, context):
        self.context = context

    def fiddle(self, schema):
        return schema
