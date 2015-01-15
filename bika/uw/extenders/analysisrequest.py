from archetypes.schemaextender.interfaces import IOrderableSchemaExtender
from archetypes.schemaextender.interfaces import ISchemaModifier
from bika.lims import bikaMessageFactory as _
from bika.lims.browser.widgets import DateTimeWidget
from bika.lims.browser.widgets import DecimalWidget as bikaDecimalWidget
from bika.lims.fields import *
from bika.lims.interfaces import IAnalysisRequest
from Products.Archetypes.public import *
from zope.component import adapts
from zope.interface import implements

# This is acquired here from batch, and acquired by Sample.
ClientSampleComment = ExtTextField(
    'ClientSampleComment',
    default_content_type='text/x-web-intelligent',
    allowable_content_types = ('text/plain', ),
    default_output_type="text/plain",
    schemata = "AnalysisRequest and Sample Fields",
    acquire=True,
    widget=TextAreaWidget(
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
        label=_('Amount Sampled'),
        visible={'view': 'visible',
                 'edit': 'visible'}
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
        label=_('Approved Exceptions To Standard Practice'),
        visible={'view': 'visible',
                 'edit': 'visible'}
    ),
)

class AnalysisRequestSchemaExtender(object):
    adapts(IAnalysisRequest)
    implements(IOrderableSchemaExtender)

    fields = [
        ClientSampleComment,
        AmountSampled,
        ExceptionalHazards,
        NonStandardMethodInstructions,
        ApprovedExceptionsToStandardPractice,
    ]

    def __init__(self, context):
        self.context = context

    def getOrder(self, schematas):
        """Return modified order of field schemats.
        """
        fields = schematas['default']
        fields.insert(fields.index('Sample') + 1, 'ApprovedExceptionsToStandardPractice')
        fields.insert(fields.index('Sample') + 1, 'NonStandardMethodInstructions')
        fields.insert(fields.index('Sample') + 1, 'ExceptionalHazards')
        fields.insert(fields.index('Sample') + 1, 'ClientSampleComment')
        fields.insert(fields.index('Sample') + 1, 'AmountSampled')

        return schematas

    def getFields(self):
        return self.fields


class AnalysisRequestSchemaModifier(object):
    adapts(IAnalysisRequest)
    implements(ISchemaModifier)

    def __init__(self, context):
        self.context = context

    def fiddle(self, schema):
        toremove = ['AdHoc',
                    'Composite',
                    'InvoiceExclude',
                    'Priority']
        for field in toremove:
            schema[field].required = False
            schema[field].widget.visible = False

        return schema
