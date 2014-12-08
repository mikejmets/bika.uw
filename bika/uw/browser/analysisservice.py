from archetypes.schemaextender.interfaces import IOrderableSchemaExtender
from archetypes.schemaextender.interfaces import ISchemaModifier
from bika.lims import bikaMessageFactory as _
from bika.lims.browser.widgets import DateTimeWidget, RecordsWidget
from bika.lims.browser.widgets import DecimalWidget as bikaDecimalWidget
from bika.lims.fields import *
from bika.lims.interfaces import IAnalysisService
from Products.Archetypes.public import *
from zope.component import adapts
from zope.interface import implements

# Storing CAS number for a service.
# Note this field is searchable=True.
# This means a proper index accessor must be defined.
CASField = ExtRecordsField(
    'CAS',
    searchable=True,
    schemata="Description",
    type='casnumber',
    subfields=('CAS', 'Title', 'Description'),
    required_subfields=('CAS', 'Title'),
    subfield_labels={'CAS': _('CAS #')},
    subfield_validators={},
    subfield_sizes={'CAS':7,
                    'Title': 20},
    widget=RecordsWidget(
        label=_("Result Options"),
        description=_(
            "Enter a list of CAS numbers and their descriptions, "
            "one per line. On each line, everything before the "
            "first space, will be used as a CAS identifier for "
            "this object."),
    ),
)

def cas_index_accessor(self, instance):
    def get(obj):
        casses = obj.Schema().getField('CAS').get(obj)
        cas_str = ""
        for c in casses:
            cas_str.append(" ".join(c['CAS'], c['Title']))
        print cas_str
        return cas_str
    return get
CASField.getIndexAccessor = cas_index_accessor


class AnalysisServiceSchemaExtender(object):
    adapts(IAnalysisService)
    implements(IOrderableSchemaExtender)

    fields = [
        CASField,
    ]

    def __init__(self, context):
        self.context = context

    def getOrder(self, schematas):
        """Return modified order of field schemats.
        """
        fields = schematas['default']
        fields.insert(fields.index('ShortTitle') + 1, 'CAS')

        return schematas

    def getFields(self):
        return self.fields


class AnalysisServiceSchemaModifier(object):
    adapts(IAnalysisService)
    implements(ISchemaModifier)

    def __init__(self, context):
        self.context = context

    def fiddle(self, schema):
        return schema
