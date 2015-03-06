from archetypes.schemaextender.interfaces import IOrderableSchemaExtender
from archetypes.schemaextender.interfaces import ISchemaModifier
from bika.lims.interfaces import IAnalysisService
from zope.component import adapts
from zope.interface import implements


class AnalysisServiceSchemaExtender(object):
    adapts(IAnalysisService)
    implements(IOrderableSchemaExtender)

    fields = [
    ]

    def __init__(self, context):
        self.context = context

    def getOrder(self, schematas):
        """Return modified order of field schema ts.
        """
        return schematas

    def getFields(self):
        return self.fields


class AnalysisServiceSchemaModifier(object):
    adapts(IAnalysisService)
    implements(ISchemaModifier)

    def __init__(self, context):
        self.context = context

    def fiddle(self, schema):
        toremove = ['MemberDiscountApplies',
                    'BulkDiscount',
                    'TaxNumber']
        for field in toremove:
            schema[field].required = False
            schema[field].widget.visible = False

        return schema
