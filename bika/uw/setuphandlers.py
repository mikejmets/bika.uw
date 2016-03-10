""" Bika setup handlers. """

from Products.CMFCore.utils import getToolByName


def addIndex(cat, *args):
    try:
        cat.addIndex(*args)
    except:
        pass


def addColumn(cat, col):
    try:
        cat.addColumn(col)
    except:
        pass


def setupVarious(context):
    """
    Final Bika import steps.
    """
    if context.readDataFile('bika.lims_various.txt') is None:
        return

    site = context.getSite()

    bac = getToolByName(site, 'bika_analysis_catalog')
    # at = getToolByName(site, 'archetype_tool')
    # at.setCatalogsByType('DuplicateAnalysis', ['bika_analysis_catalog'])
    # addIndex(bac, 'path', 'ExtendedPathIndex', ('getPhysicalPath'))
    # addColumn(bac, 'path')
    bc = getToolByName(site, 'bika_catalog', )
    # at = getToolByName(site, 'archetype_tool')
    # at.setCatalogsByType('Worksheet', ['bika_catalog'])
    # addIndex(bc, 'path', 'ExtendedPathIndex', ('getPhysicalPath'))
    # addColumn(bc, 'review_state')
    bsc = getToolByName(site, 'bika_setup_catalog', None)
    # at = getToolByName(site, 'archetype_tool')
    # at.setCatalogsByType('ARPriority', ['bika_setup_catalog', ])
    # addIndex(bsc, 'getObjPositionInParent', 'GopipIndex')
    # addColumn(bsc, 'path')

    # Plone's jQuery gets clobbered when jsregistry is loaded.
    setup = site.portal_setup
    setup.runImportStepFromProfile(
        'profile-plone.app.jquery:default', 'jsregistry')
    # setup.runImportStepFromProfile('profile-plone.app.jquerytools:default', 'jsregistry')

