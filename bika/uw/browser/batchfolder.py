from bika.lims import bikaMessageFactory as _
from bika.lims.browser.batchfolder import BatchFolderContentsView as BaseView


class BatchFolderContentsView(BaseView):
    """Override the default listing of batches.

    - Display additional review state filter buttons.
    - Additional columns available for display.
    """

    def __init__(self, context, request):
        import pdb, sys; pdb.Pdb(stdout=sys.__stdout__).set_trace()
        super(BatchFolderContentsView, self).__init__(context, request)
        self.title = _("Batches")
        self.description = "testing"
        self.review_states = [
            {'id':'requested',
             'contentFilter': {'review_state': 'requested', 'sort_on':'created', 'sort_order': 'reverse'},
             'title': _('Requested'),
             'columns': self.columns},
            {'id':'approved',
             'contentFilter': {'review_state': 'approved', 'sort_on':'created', 'sort_order': 'reverse'},
             'title': _('Approved'),
             'columns': self.columns},
            {'id':'received',
             'contentFilter': {'review_state': 'received', 'sort_on':'created', 'sort_order': 'reverse'},
             'title': _('Recieved'),
             'columns': self.columns},
            {'id':'accepted',
             'contentFilter': {'review_state': 'accepted', 'sort_on':'created', 'sort_order': 'reverse'},
             'title': _('Accepted'),
             'columns': self.columns},
            {'id':'released',
             'contentFilter': {'review_state': 'released', 'sort_on':'created', 'sort_order': 'reverse'},
             'title': _('Released'),
             'columns': self.columns},
            {'id':'prepared',
             'contentFilter': {'review_state': 'prepared', 'sort_on':'created', 'sort_order': 'reverse'},
             'title': _('Prepared'),
             'columns': self.columns},
            {'id':'tested',
             'contentFilter': {'review_state': 'tested', 'sort_on':'created', 'sort_order': 'reverse'},
             'title': _('Tested'),
             'columns': self.columns},
            {'id':'passed_qa',
             'contentFilter': {'review_state': 'passed_qa', 'sort_on':'created', 'sort_order': 'reverse'},
             'title': _('Passed QA'),
             'columns': self.columns},
            {'id':'published',
             'contentFilter': {'review_state': 'published', 'sort_on':'created', 'sort_order': 'reverse'},
             'title': _('Published'),
             'columns': self.columns},
            {'id':'cancelled',
             'title': _('Cancelled'),
             'contentFilter': {'cancellation_state': 'cancelled', 'sort_on':'created', 'sort_order': 'reverse'},
             'columns': self.columns},
            {'id':'all',
             'contentFilter': {'sort_on':'created', 'sort_order': 'reverse'},
             'title': _('All'),
             'columns': self.columns},
        ]

    def __call__(self):
        return super(BatchFolderContentsView, self).__call__()
