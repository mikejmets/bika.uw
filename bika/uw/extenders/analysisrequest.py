from archetypes.schemaextender.interfaces import IOrderableSchemaExtender
from archetypes.schemaextender.interfaces import ISchemaModifier
from zope.component import adapts

from bika.lims import bikaMessageFactory as _
from bika.lims.fields import *
from bika.lims.interfaces import IAnalysisRequest

# This is acquired here from batch, and acquired by Sample.
ClientSampleComment = ExtTextField(
    'ClientSampleComment',
    default_content_type='text/x-web-intelligent',
    allowable_content_types = ('text/plain', ),
    default_output_type="text/plain",
    schemata = "AnalysisRequest and Sample Fields",
    acquire=True,
    widget=TextAreaWidget(
        render_own_label=True,
        label=_('Client Sample Comment'),
        description=_("These comments will be applied as defaults in Client Remarks field for new Samples."),
    )
)

# This is acquired here from batch, and acquired by Sample.
AmountSampled = ExtStringField(
    'AmountSampled',
    required=False,
    schemata = "Work Order Instructions",
    acquire=True,
    widget=StringWidget(
        render_own_label=True,
        label=_('Amount Sampled'),
        visible={'view': 'visible',
                 'edit': 'visible',
                 'header_table': 'visible'}
    ),
)

# This is acquired here from batch, and acquired by Sample.
AmountSampledMetric = ExtStringField(
    'AmountSampledMetric',
    required=False,
    schemata = "Work Order Instructions",
    acquire=True,
    widget=StringWidget(
        render_own_label=True,
        label=_('Amount Sampled Metric'),
        visible={'view': 'visible',
                 'edit': 'visible',
                 'header_table': 'visible'}
    ),
)

# This is acquired here from batch, and acquired by Sample.
ExceptionalHazards = ExtTextField(
    'ExceptionalHazards',
    default_content_type='text/x-web-intelligent',
    allowable_content_types = ('text/plain', ),
    default_output_type="text/plain",
    schemata = "Hazards",
    acquire=True,
    widget=TextAreaWidget(
        render_own_label=True,
        label=_('Exceptional hazards'),
        description=_("The value selected here will be set as the default for new Samples."),
    )
)

# This is acquired here from batch
NonStandardMethodInstructions = ExtTextField(
    'NonStandardMethodInstructions',
    required=False,
    schemata = "Work Order Instructions",
    acquire=True,
    widget=TextAreaWidget(
        render_own_label=True,
        label=_('Non-standard Method Instructions'),
        visible={'view': 'visible',
                 'edit': 'visible'}
    ),
)

# This is acquired here from batch
ApprovedExceptionsToStandardPractice = ExtTextField(
    'ApprovedExceptionsToStandardPractice',
    required=False,
    schemata = "Work Order Instructions",
    acquire=True,
    widget=TextAreaWidget(
        render_own_label=True,
        label=_('Approved Exceptions To Standard Practice'),
        visible={'view': 'visible',
                 'edit': 'visible'}
    ),
)

# This is acquired here from batch, and acquired by Sample.
SampleSite = ExtStringField(
        'SampleSite',
        schemata="AnalysisRequest and Sample Fields",
        acquire=True,
        widget=StringWidget(
                render_own_label=True,
                label=_('Sample Site'),
                size=20,
                description=_("The sample site for an AR's Sample."),
                visible={'view': 'visible',
                         'edit': 'visible',
                         'add': 'edit',
                         'header_table': 'visible'}
        )
)

class AnalysisRequestSchemaExtender(object):
    adapts(IAnalysisRequest)
    implements(IOrderableSchemaExtender)

    fields = [
        ClientSampleComment,
        AmountSampled,
        AmountSampledMetric,
        ExceptionalHazards,
        NonStandardMethodInstructions,
        ApprovedExceptionsToStandardPractice,
        SampleSite,
    ]

    def __init__(self, context):
        self.context = context

    def getOrder(self, schematas):
        """Return modified order of field schemats.
        """

        index = schematas['default'].index('SampleType') + 1
        schematas['default'].insert(index,
                                    'ApprovedExceptionsToStandardPractice')
        schematas['default'].insert(index, 'NonStandardMethodInstructions')
        schematas['default'].insert(index, 'ExceptionalHazards')
        schematas['default'].insert(index, 'ClientSampleComment')
        schematas['default'].insert(index, 'AmountSampled')
        schematas['default'].insert(index, 'SampleSite')

        return schematas

    def getFields(self):
        return self.fields


class AnalysisRequestSchemaModifier(object):

    adapts(IAnalysisRequest)
    implements(ISchemaModifier)

    def __init__(self, context):
        self.context = context

    def fiddle(self, schema):

        hidden = ['AdHoc',
                  'Composite',
                  'InvoiceExclude',
                  'Priority',
                  'SamplePoint']
        for field in hidden:
            schema[field].required = False
            schema[field].widget.visible = False
        # I want to remove Sample from AR add.
        # This way secondary samples are not disabled, just the UI is.
        schema['Sample'].required = False
        schema['Sample'].widget.visible = {
            'edit': 'invisible',
            'view': 'invisible',
            'add': 'hidden',
        }
        schema.moveField('SampleSite', before='SampleType')

        return schema
