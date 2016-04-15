from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFCore.utils import getToolByName
from bika.lims import logger
from bika.lims.utils import changeWorkflowState


def batch_receive(instance):
    """When a batch is recieved, all associated ARs must be received.
      (normal AR workflow cascade will transition samples, analyses, etc)
    """
    workflow = getToolByName(instance, 'portal_workflow')
    for ar in instance.getAnalysisRequests():
        try:
            workflow.doActionFor(ar, 'receive')
        except WorkflowException:
            logger.info("batch_receive: could not execute receive on %s" % ar.id)


def batch_test(instance):
    workflow = getToolByName(instance, 'portal_workflow')
    for ar in instance.getAnalysisRequests():
        for a in ar.getAnalyses(full_objects=True):
            changeWorkflowState(a, 'bika_analysis_workflow', 'to_be_verified')
        changeWorkflowState(ar, 'bika_ar_workflow', 'to_be_verified')

def batch_pass_qa(instance):
    workflow = getToolByName(instance, 'portal_workflow')
    for ar in instance.getAnalysisRequests():
        for a in ar.getAnalyses(full_objects=True):
            changeWorkflowState(a, 'bika_analysis_workflow', 'verified')
        changeWorkflowState(ar, 'bika_ar_workflow', 'verified')


def batch_publish(instance):
    workflow = getToolByName(instance, 'portal_workflow')
    for ar in instance.getAnalysisRequests():
        for a in ar.getAnalyses(full_objects=True):
            changeWorkflowState(a, 'bika_analysis_workflow', 'published')
        changeWorkflowState(ar, 'bika_ar_workflow', 'published')


def AfterTransitionEventHandler(instance, event):
    # creation doesn't have a 'transition':
    if not event.transition:
        return

    if event.transition.id == 'batch_receive':
        batch_receive(instance)
    elif event.transition.id == 'batch_test':
        batch_test(instance)
    elif event.transition.id == 'batch_pass_qa':
        batch_pass_qa(instance)
    elif event.transition.id == 'batch_publish':
        batch_publish(instance)
