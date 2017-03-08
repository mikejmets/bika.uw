from Products.Archetypes.Widget import StringWidget
from archetypes.schemaextender.interfaces import IOrderableSchemaExtender
from archetypes.schemaextender.interfaces import ISchemaModifier
from bika.lims.fields import ExtStringField
from bika.lims.interfaces import IARImport
from Products.CMFCore import permissions
from zope.component import adapts
from zope.interface import implements

from bika.lims import bikaMessageFactory as _

HIDDEN_FIELDS = ['SamplePoint',]

SampleSite = ExtStringField(
    'SampleSite',
    searchable=True,
    mode="rw",
    read_permission=permissions.View,
    write_permission=permissions.ModifyPortalContent,
    widget=StringWidget(
        label=_('Sample Site'),
        description=_("Text describing the site the sample was taken from"),
        size=20,
        visible={'edit': 'visible', 'view': 'visible',},
    ),
)


class ARImportSchemaExtender(object):
    adapts(IARImport)
    implements(IOrderableSchemaExtender)

    fields = [
        SampleSite,
    ]

    def __init__(self, context):
        self.context = context

    def getOrder(self, schematas):
        """Return modified order of field schemats.
        """
        index = schematas['default'].index('SamplePoint') + 1
        schematas['default'].insert(index, 'SampleSite')
        return schematas

    def getFields(self):
        return self.fields


class ARImportSchemaModifier(object):
    adapts(IARImport)
    implements(ISchemaModifier)

    def __init__(self, context):
        self.context = context

    def fiddle(self, schema):
        for field in HIDDEN_FIELDS:
            schema[field].required = False
            schema[field].widget.visible = False

        return schema







