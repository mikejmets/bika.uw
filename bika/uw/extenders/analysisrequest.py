from Products.CMFPlone.interfaces import IPloneSiteRoot
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
        size=20,
        label=_('Amount Sampled'),
        visible={'view': 'visible',
                 'edit': 'visible',
                 'header_table': 'visible',
                 'add': 'edit'}
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
        size=20,
        label=_('Amount Sampled Metric'),
        visible={'view': 'visible',
                 'edit': 'visible',
                 'header_table': 'visible',
                 'add': 'edit'}
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

class SampleSiteField(ExtStringField):
    """A computed field which sets and gets a value from Sample
    """

    def get(self, instance):
        sample = instance.getSample()
        value = False
        if sample:
            value = sample.Schema()['SampleSite'].get(sample)
        if not value:
            value = self.getDefault(instance)
        return value

    def set(self, instance, value):
        sample = instance.getSample()
        if sample and value:
            return sample.Schema()['SampleSite'].set(sample, value)

    def getDefault(self, instance):
        current = instance
        while hasattr(current, 'aq_parent'):
            current = current.aq_parent
            if IPloneSiteRoot.providedBy(current):
                break
            schema = current.Schema()
            if 'SampleSite' in schema._names:
                value = schema['SampleSite'].get(current)
                if value is not None:
                    return value


# This is acquired here from batch, and acquired by Sample.
SampleSite = SampleSiteField(
        'SampleSite',
        schemata="AnalysisRequest and Sample Fields",
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
        ExceptionalHazards,
        NonStandardMethodInstructions,
        ApprovedExceptionsToStandardPractice,
        SampleSite,
        AmountSampled,
        AmountSampledMetric,
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
        schematas['default'].insert(index, 'SampleSite')

        index = schematas['AnalysisRequest and Sample Fields'].index('BioHazardous')
        schematas['AnalysisRequest and Sample Fields'].insert(index, 'AmountSampledMetric')
        schematas['AnalysisRequest and Sample Fields'].insert(index, 'AmountSampled')

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
                  'SamplePoint',
                  'ClientReference',
                  'SubGroup',
                  'Specification',
                  'SamplingDeviation',
                  'SampleCondition',
                  'PreparationWorkflow',
                  ]
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
