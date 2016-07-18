from zope.interface import implements

from bika.lims.interfaces import IATWidgetVisibility, IClient


class BatchARAddFieldsWidgetVisibility(object):
    """per LIMS-2238 some fields get hidden in batch context during AR create
    """
    implements(IATWidgetVisibility)

    def __init__(self, context):
        self.context = context
        self.sort = 10

    def __call__(self, context, mode, field, default):
        hidden = [
            # LIMS-2238 remove these from AR add:
            'CCContact',
            'CCEmails',
            'ClientOrderNumber',
            'Template',
        ]
        state = default if default else 'visible'
        fieldName = field.getName()
        if mode == 'add' and fieldName in hidden:
            if context.aq_parent.portal_type == 'Batch' and fieldName in hidden:
                state = 'hidden'
        return state
