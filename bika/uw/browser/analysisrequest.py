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

class BatchSchemaExtender(object):
    adapts(IBatch)
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

        >>> portal = layer['portal']
        >>> portal_url = portal.absolute_url()
        >>> from plone.app.testing import SITE_OWNER_NAME
        >>> from plone.app.testing import SITE_OWNER_PASSWORD

        We must test that the SampleTemperature field exists, because we
        use it to position our fields.

        >>> browser = layer['getBrowser'](portal, loggedIn=True, username=SITE_OWNER_NAME, password=SITE_OWNER_PASSWORD)
        >>> browser.open(portal_url+"/batches/portal_factory/Batch/new_batch/edit")
        >>> 'Sample Temperature' in browser.contents
        True
        """
        fields = schematas['default']
        fields.insert(fields.index('SampleTemperature') + 1, 'ClientSampleComment')
        fields.insert(fields.index('') + 1, '')

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
