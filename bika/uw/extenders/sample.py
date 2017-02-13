from Products.Archetypes.public import *
from archetypes.schemaextender.interfaces import IOrderableSchemaExtender
from archetypes.schemaextender.interfaces import ISchemaModifier
from zope.component import adapts
from zope.interface import implements

from bika.lims import bikaMessageFactory as _
from bika.lims.fields import *
from bika.lims.interfaces import ISample

from bika.lims.browser.widgets import ReferenceWidget as brw

# This is acquired here from batch, and acquired by Sample.
ClientSampleComment = ExtTextField(
    'ClientSampleComment',
    default_content_type='text/x-web-intelligent',
    allowable_content_types=('text/plain',),
    default_output_type="text/plain",
    acquire=True,
    widget=TextAreaWidget(
        render_own_label=True,
        label=_('Client Sample Comment'),
        description=_(
            "These comments will be applied as defaults in Client Remarks "
            "field for new Samples."),
    )
)

# This is acquired here from batch, and acquired by Sample.
AmountSampled = ExtStringField(
    'AmountSampled',
    required=False,
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
    allowable_content_types=('text/plain',),
    default_output_type="text/plain",
    acquire=True,
    widget=TextAreaWidget(
        render_own_label=True,
        label=_('Exceptional hazards'),
        description=_(
            "The value selected here will be set as the default for new "
            "Samples."),
    )
)

SampleSite = ExtStringField(
        'SampleSite',
        searchable=True,
        required=0,
        widget=StringWidget(
            render_own_label=True,
            visible={'edit': 'visible',
                         'view': 'visible',
                         'add': 'edit',
                         'header_table': 'visible',
                         'sample_registered': {'view': 'invisible', 'edit': 'invisible', 'add': 'edit'},
                         'to_be_sampled':     {'view': 'invisible', 'edit': 'invisible'},
                         'sampled':           {'view': 'invisible', 'edit': 'invisible'},
                         'sample_prep':       {'view': 'invisible', 'edit': 'invisible'},
                         'to_be_preserved':   {'view': 'invisible', 'edit': 'invisible'},
                         'sample_received':   {'view': 'invisible', 'edit': 'invisible'},
                         'attachment_due':    {'view': 'invisible', 'edit': 'invisible'},
                         'to_be_verified':    {'view': 'invisible', 'edit': 'invisible'},
                         'verified':          {'view': 'invisible', 'edit': 'invisible'},
                         'published':         {'view': 'invisible', 'edit': 'invisible'},
                         'invalid':           {'view': 'invisible', 'edit': 'invisible'},
                         },
                label=_("Sample Site"),
                description=_("This sample's Sample Site."),
        )
)

# This is acquired here from AR, who acquires default value from Batch.
Container = ExtReferenceField(
    'Container',
    required=False,
    allowed_types=('Container',),
    relationship='SampleContainer',
    acquire=True,
    widget=brw(
        label=_('Container'),
        description=_('Container used for this sample.'),
        size=20,
        render_own_label=True,
        visible={'edit': 'visible',
                 'view': 'visible',
                 'add': 'edit',
                 'header_table': 'visible',
                 'sample_registered':
                     {'view': 'invisible', 'edit': 'invisible', 'add': 'edit'},
                 'to_be_sampled': {'view': 'invisible', 'edit': 'invisible'},
                 'sampled': {'view': 'invisible', 'edit': 'invisible'},
                 'sample_prep': {'view': 'invisible', 'edit': 'invisible'},
                 'to_be_preserved': {'view': 'invisible', 'edit': 'invisible'},
                 'sample_received': {'view': 'invisible', 'edit': 'invisible'},
                 'attachment_due': {'view': 'invisible', 'edit': 'invisible'},
                 'to_be_verified': {'view': 'invisible', 'edit': 'invisible'},
                 'verified': {'view': 'invisible', 'edit': 'invisible'},
                 'published': {'view': 'invisible', 'edit': 'invisible'},
                 'invalid': {'view': 'invisible', 'edit': 'invisible'},
                 },
        catalog_name='bika_setup_catalog',
        base_query={'inactive_state': 'active'},
        showOn=True,
    ),
)


class SampleSchemaExtender(object):
    adapts(ISample)
    implements(IOrderableSchemaExtender)

    fields = [
        ClientSampleComment,
        AmountSampled,
        AmountSampledMetric,
        Container,
        ExceptionalHazards,
        SampleSite,
    ]

    def __init__(self, context):
        self.context = context

    def getOrder(self, schematas):
        """Return modified order of field schemats.
        """
        fields = schematas['default']
        fields.insert(fields.index('SampleType') + 1, 'SampleSite')
        fields.insert(fields.index('SamplePoint') + 1, 'ExceptionalHazards')
        fields.insert(fields.index('SamplePoint') + 1, 'ClientSampleComment')
        fields.insert(fields.index('SamplePoint') + 1, 'AmountSampled')

        return schematas

    def getFields(self):
        return self.fields


class SampleSchemaModifier(object):
    adapts(ISample)
    implements(ISchemaModifier)

    def __init__(self, context):
        self.context = context

    def fiddle(self, schema):
        toremove = ['SamplePoint']
        for field in toremove:
            schema[field].required = False
            schema[field].widget.visible = False

        # LIMS-1378
        # These fields from bika.lims will be flagged as acquired=True,
        # and have corrosponding fields in bika.uw/extenders/batch.py
        acquired = [
            'ReturnSampleToClient',
            'Hazardous',
            'SampleTemperature',
            'DateSampled',
            'Sampler',
            'PreparationWorkflow',
            'SamplingDeviation',
            'SampleCondition']
        for field in acquired:
            if field in schema:
                schema[field].acquire = True
