import json

from bika.lims.browser import BrowserView

import plone


class ajaxGetContacts(BrowserView):
    """ Vocabulary source for jquery combo dropdown box
    """

    def __init__(self, context, request):
        BrowserView.__init__(self, context, request)

    def __call__(self):
        plone.protect.CheckAuthenticator(self.request)
        searchTerm = self.request.get('searchTerm', '').lower()
        page = self.request.get('page', 1)
        nr_rows = self.request.get('rows', 20)

        contacts = self.context.aq_parent.objectValues('Contact')
        if searchTerm:
            rows = [{'Fullname': c.Title()} for c in contacts
                    if c.getFullname().lower() == searchTerm.lower()]
        else:
            rows = [{'Fullname': c.Title()} for c in contacts]

        pages = len(rows) / int(nr_rows)
        pages += divmod(len(rows), int(nr_rows))[1] and 1 or 0
        ret = {'page': page,
               'total': pages,
               'records': len(rows),
               'rows': rows[(int(page) - 1) * int(nr_rows): int(page) * int(
                   nr_rows)]}

        return json.dumps(ret)

