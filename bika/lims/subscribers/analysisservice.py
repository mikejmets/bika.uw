from DateTime import DateTime
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFCore.utils import getToolByName
from bika.lims import bikaMessageFactory as _
import transaction

def ActionSucceededEventHandler(instance, event):

    wf = getToolByName(instance, 'portal_workflow')
    pc = getToolByName(instance, 'portal_catalog')
    rc = getToolByName(instance, 'reference_catalog')
    pu = getToolByName(instance, 'plone_utils')

    if event.action == "deactivate":
        # A service cannot be deactivated if "active" calculations list it
        # as a dependency.
        calculations = (c.getObject() for c in \
                        pc(portal_type='Calculation', inactive_review_state="active"))
        for calc in calculations:
            deps = [dep.UID() for dep in calc.getDependentServices()]
            if instance.UID() in deps:
                message = _("This Analysis Service cannot be deactivated "
                            "because one or more active calculations list "
                            "it as a dependency")
                pu.addPortalMessage(message, 'error')
                transaction.get().abort()
                raise WorkflowException

    if event.action == "activate":
        # A service cannot be activated if it's calculation is inactive
        calc = instance.getCalculation()
        if calc and \
           wf.getInfoFor(calc, "inactive_review_state") == "inactive":
            message = _("This Analysis Service cannot be activated "
                        "because it's calculation is inactive.")
            pu.addPortalMessage(message, 'error')
            transaction.get().abort()
            raise WorkflowException