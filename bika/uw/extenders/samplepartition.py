from archetypes.schemaextender.interfaces import ISchemaModifier
from zope.component import adapts

from bika.lims.fields import *
from bika.lims.interfaces import ISamplePartition


class SamplePartitionSchemaModifier(object):
    adapts(ISamplePartition)
    implements(ISchemaModifier)

    def __init__(self, context):
        self.context = context

    def fiddle(self, schema):
        schema['Container'].acquire = True
