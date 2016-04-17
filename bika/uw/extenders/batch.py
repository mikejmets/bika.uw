from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFPlone.interfaces import IPloneSiteRoot
from archetypes.schemaextender.interfaces import IOrderableSchemaExtender
from archetypes.schemaextender.interfaces import ISchemaModifier
from bika.lims import bikaMessageFactory as _
from bika.lims.browser import ulocalized_time as ut
from bika.lims.browser.widgets import DateTimeWidget
from bika.lims.browser.widgets import ReferenceWidget as brw
from bika.lims.fields import *
from bika.lims.interfaces import IBatch, IClient
from plone import api
from Products.Archetypes.public import *
from Products.CMFCore import permissions
from Products.CMFCore.utils import getToolByName
from zope.component import adapts

import sys
from bika.lims.utils import getUsers


class WorkflowDateField(ExtStringField):
    """Used to show workflow history dates as Field Values in the UI.
    """

    def get(self, instance):
        """This getter contains a simple lookup table; The most recent
        review_history entry's 'time' value will be used, where
        state_title == workflow_state_id
        """
        field_state_lookup = {
            'DateApproved': 'approved',
            'DateReceived': 'received',
            'DateAccepted': 'accepted',
            'DateReleased': 'released',
            'DatePrepared': 'prepared',
            'DateTested': 'tested',
            'DatePassedQA': 'passed_qa',
            'DatePublished': 'published',
            'DateCancelled': 'cancelled',
        }
        workflow = getToolByName(instance, 'portal_workflow')
        try:
            review_history = list(workflow.getInfoFor(instance, 'review_history'))
        except WorkflowException:
            # Maybe there is no review_history at some states.  If it doesn't
            # exist, we can't care about it.
            review_history = []
        # invert the list, so we always see the most recent matching event
        review_history.reverse()
        try:
            state_id = field_state_lookup[self.getName()]
        except:
            raise RuntimeError("field %s.%s not in field_state_lookup" %
                               instance, self.getName())
        for event in review_history:
            if event['review_state'] == state_id:
                value = ut(event['time'],
                           long_format=True,
                           time_only=False,
                           context=instance)
                return value
        return None

    def set(self, instance, value):
        return


class RetractionDatesField(ExtLinesField):
    """Show a list of all retractions on all ARs in this Work Order
    """

    def get(self, instance):
        """This getter returns a multiline string, each line contains:
        <Analysis Request> <Analysis Service> <actor> <time>
        """
        workflow = getToolByName(instance, 'portal_workflow')

        result = []
        for ar in instance.getAnalysisRequests():
            for analysis in ar.getAnalyses(full_objects=True):
                review_history = list(workflow.getInfoFor(analysis,
                                                          'review_history'))
                review_history.reverse()
                for event in review_history:
                    if event['review_state'] == "retracted":
                        result.append("%-20s %-20s %-10s %s" % (
                            ar.getId(),
                            analysis.getId(),
                            '' if event['actor'] is None else event['actor'],
                            ut(event['time'],
                               long_format=True,
                               time_only=False,
                               context=instance)
                        ))
        return result


##############################################################################
##############################################################################
# Batch fields which are used as default values for Sample and AR

Contact = ExtReferenceField(
    'Contact',
    required=0,
    vocabulary_display_path_bound=sys.maxsize,
    allowed_types=('Contact',),
    relationship='BatchContact',
    mode="rw",
    read_permission=permissions.View,
    write_permission=permissions.ModifyPortalContent,
    widget=brw(
        label=_("Contact"),
        description=_("The Client Contact person for this batch"),
        size=20,
        helper_js=("bika_widgets/referencewidget.js",),
        visible={'edit': 'visible', 'view': 'visible'},
        base_query={'inactive_state': 'active'},
        showOn=True,
        popup_width='400px',
        colModel=[{'columnName': 'UID', 'hidden': True},
                  {'columnName': 'Fullname', 'width': '50',
                   'label': _('Name')},
                  {'columnName': 'EmailAddress', 'width': '50',
                   'label': _('Email Address')},
                  ],
    ),
)

CCContact = ExtReferenceField(
    'CCContact',
    required=0,
    multiValued=True,
    vocabulary_display_path_bound=sys.maxsize,
    allowed_types=('Contact',),
    relationship='BatchCCContact',
    mode="rw",
    read_permission=permissions.View,
    write_permission=permissions.ModifyPortalContent,
    widget=brw(
        label=_("CC Contact"),
        description=_("These Client Contacts will be copied in email "
                      "communication regarding this batch, e.g. receive "
                      "emailed results"),
        size=20,
        helper_js=("bika_widgets/referencewidget.js",),
        visible={'edit': 'visible',
                 'view': 'visible',
                 },
        base_query={'inactive_state': 'active'},
        showOn=True,
        popup_width='400px',
        colModel=[{'columnName': 'UID', 'hidden': True},
                  {'columnName': 'Fullname',
                   'width': '50',
                   'label': _('Name')},
                  {'columnName': 'EmailAddress',
                   'width': '50',
                   'label': _('Email Address')},
                  ],
    ),
)

CCEmails = ExtLinesField(
    'CCEmails',
    searchable=True,
    required=0,
    widget=LinesWidget(
        rows=5,
        cols=20,
        style="width:25ex;font-size:85%;",  # ! XXX
        label=_("CC Emails"),
        description=_("Add further email addresses to be copied"),
    )
)

InvoiceContact = ExtReferenceField(
    'InvoiceContact',
    required=0,
    vocabulary_display_path_bound=sys.maxsize,
    allowed_types=('Contact',),
    relationship='BatchInvoiceContact',
    mode="rw",
    read_permission=permissions.View,
    write_permission=permissions.ModifyPortalContent,
    widget=brw(
        label=_("Invoice Contact"),
        description=_(
            "The Client Contact to whom invoices for this batch "
            "will be sent"),
        size=20,
        helper_js=("bika_widgets/referencewidget.js",),
        visible={'edit': 'visible',
                 'view': 'visible',
                 },
        base_query={'inactive_state': 'active'},
        showOn=True,
        popup_width='400px',
        colModel=[{'columnName': 'UID', 'hidden': True},
                  {'columnName': 'Fullname',
                   'width': '50',
                   'label': _('Name')},
                  {'columnName': 'EmailAddress',
                   'width': '50',
                   'label': _('Email Address')},
                  ],
    ),
)

Analysts = ExtLinesField(
    'Analysts',
    multiValued=True,
    size=8,
    mode="rw",
    read_permission=permissions.View,
    write_permission=permissions.ModifyPortalContent,
    vocabulary_factory="bika.lims.vocabularies.Analysts",
    widget=MultiSelectionWidget(
        format='select',
        label=_("Analysts"),
        description=_("The analysts that are assigned to the batch"),
        visible={'edit': 'visible',
                 'view': 'visible',
                 },
    ),
)

LeadAnalyst = ExtStringField(
    'LeadAnalyst',
    mode="rw",
    read_permission=permissions.View,
    write_permission=permissions.ModifyPortalContent,
    vocabulary_factory="bika.lims.vocabularies.Analysts",
    widget=SelectionWidget(
        format='select',
        label=_("Lead Analyst"),
        description=_(
            "The analyst responsible for the analyses and QC of "
            "this batch"),
        visible={'edit': 'visible',
                 'view': 'visible',
                 },
    ),
)

ClientProjectName = ExtStringField(
    'ClientProjectName',
    searchable=True,
    required=0,
    widget=StringWidget(
        label=_("Client Project Name"),
        description=_(
            "The project name the client provided for the batch"),
    )
)

SampleSource = ExtStringField(
    'SampleSource',
    searchable=True,
    required=0,
    widget=StringWidget(
        label=_("Sample Source"),
        description=_("The Work Order sample source"),
    )
)

SampleSite = ExtStringField(
    'SampleSite',
    searchable=True,
    required=0,
    widget=StringWidget(
        label=_("Sample Site"),
        description=_(
            "A default Sample Site for ARs and Samples in this work order.  The individual objects can override this."),
        visible={'edit': 'visible',
                 'view': 'visible',
                 },
    )
)

SampleType = ExtReferenceField(
    'SampleType',
    required=0,
    allowed_types='SampleType',
    relationship='BatchSampleType',
    mode="rw",
    read_permission=permissions.View,
    write_permission=permissions.ModifyPortalContent,
    widget=brw(
        label=_("Sample Type"),
        description=_("Create a new sample of this type"),
        size=20,
        visible={'edit': 'visible',
                 'view': 'visible',
                 'add': 'edit',
                 },
        catalog_name='bika_setup_catalog',
        base_query={'inactive_state': 'active'},
        showOn=True,
    ),
)

SampleMatrix = ExtReferenceField(
    'SampleMatrix',
    required=False,
    allowed_types='SampleMatrix',
    relationship='BatchSampleMatrix',
    mode="rw",
    read_permission=permissions.View,
    write_permission=permissions.ModifyPortalContent,
    widget=brw(
        label=_("Sample Matrix"),
        description=_(
            "The sample matrix the sample is 'categorised' in"),
        size=20,
        visible={'edit': 'visible',
                 'view': 'visible',
                 },
        catalog_name='bika_setup_catalog',
        base_query={'inactive_state': 'active'},
        showOn=True,
    ),
)

Profile = ExtReferenceField(
    'Profile',
    allowed_types=('AnalysisProfile',),
    relationship='BatchAnalysisProfile',
    mode="rw",
    read_permission=permissions.View,
    write_permission=permissions.ModifyPortalContent,
    widget=brw(
        label=_("Analysis Profile"),
        description=_(
            "Auto select all the analyses included in the profile "
            "or 'panel'"),
        size=20,
        visible={'edit': 'visible',
                 'view': 'visible',
                 },
        catalog_name='bika_setup_catalog',
        base_query={'inactive_state': 'active'},
        showOn=True,
    ),
)

Container = ExtReferenceField(
    'Container',
    allowed_types=('Container',),
    relationship='AnalysisRequestContainer',
    mode="rw",
    read_permission=permissions.View,
    write_permission=permissions.ModifyPortalContent,
    widget=brw(
        label=_('Default Container'),
        description=_('Default container for new sample partitions'),
        size=20,
        visible={'edit': 'visible',
                 'view': 'visible',
                 },
        catalog_name='bika_setup_catalog',
        base_query={'inactive_state': 'active'},
        showOn=True,
    ),
)

ClientPONumber = ExtStringField(
    'ClientPONumber',
    searchable=True,
    mode="rw",
    read_permission=permissions.View,
    write_permission=permissions.ModifyPortalContent,
    widget=StringWidget(
        label=_('Client PO Number'),
        description=_(
            "The purchase order number provided by the client"),
        size=20,
        visible={'edit': 'visible',
                 'view': 'visible',
                 },
    ),
)

ClientBatchComment = ExtTextField(
    'ClientBatchComment',
    default_content_type='text/x-web-intelligent',
    allowable_content_types=('text/plain',),
    default_output_type="text/plain",
    widget=TextAreaWidget(
        label=_('Client Batch Comment'),
        description=_(
            "Additional comment to the batch provided by the client"),
    )
)

DateSampled = ExtDateTimeField(
    'DateSampled',
    mode="rw",
    read_permission=permissions.View,
    write_permission=permissions.ModifyPortalContent,
    widget=DateTimeWidget(
        label=_("Date Sampled"),
        size=20,
        visible={'edit': 'visible',
                 'view': 'visible',
                 },
    )
)

StorageLocation = ExtReferenceField(
    'StorageLocation',
    allowed_types='StorageLocation',
    relationship='AnalysisRequestStorageLocation',
    mode="rw",
    read_permission=permissions.View,
    write_permission=permissions.ModifyPortalContent,
    widget=brw(
        label=_("Storage Location"),
        description=_("Location where sample is kept"),
        size=20,
        visible={'edit': 'visible',
                 'view': 'visible',
                 },
        catalog_name='bika_setup_catalog',
        base_query={'inactive_state': 'active'},
        showOn=True,
    ),
)

ReturnSampleToClient = ExtBooleanField(
    'ReturnSampleToClient',
    widget=BooleanWidget(
        label=_("Return Sample To Client"),
        description=_("Select to indicate whether the sample must "
                      "be returned to the client"),
    )
)

SampleTemperature = ExtStringField(
    'SampleTemperature',
    widget=StringWidget(
        label=_('Sample Temperature'),
        description=_("The temperature of the individual samples"),
    )
)

SampleCondition = ExtReferenceField(
    'SampleCondition',
    vocabulary_display_path_bound=sys.maxsize,
    allowed_types=('SampleCondition',),
    relationship='BatchSampleCondition',
    mode="rw",
    read_permission=permissions.View,
    write_permission=permissions.ModifyPortalContent,
    widget=brw(
        label=_("Sample Condition"),
        description=_(
            "The condition of the individual samples on arrival"),
        visible={'edit': 'visible',
                 'view': 'visible',
                 },
        catalog_name='bika_setup_catalog',
        base_query={'inactive_state': 'active'},
        showOn=True,
    ),
)

BioHazardous = ExtBooleanField(
    'BioHazardous',
    widget=BooleanWidget(
        label=_("Hazardous"),
    )
)

Methods = ExtReferenceField(
    'Methods',
    required=0,
    multiValued=True,
    allowed_types=('Method',),
    relationship='BatchMethods',
    mode="rw",
    read_permission=permissions.View,
    write_permission=permissions.ModifyPortalContent,
    widget=brw(
        label=_("Methods"),
        description=_("Methods available for analyses in this batch"),
        visible={'edit': 'visible',
                 'view': 'visible',
                 },
        base_query={'inactive_state': 'active'},
        catalog_name='bika_setup_catalog',
        showOn=True,
        popup_width='600px',
        colModel=[{'columnName': 'UID', 'hidden': True},
                  {'columnName': 'Title',
                   'width': '100',
                   'label': _('Title'),
                   'align': 'left'},
                  ],
    ),
)

##############################################################################
##############################################################################
# Date fields

DateApproved = WorkflowDateField(
    'DateApproved',
    widget=ComputedWidget(
        label=_('Date Approved'),
        description=_('The date the Work Order was approved.'),
        visible={'view': 'visible',
                 'edit': 'visible'}
    )
)

DateReceived = WorkflowDateField(
    'DateReceived',
    readonly=True,
    widget=ComputedWidget(
        label=_('Date Received'),
        description=_('Shows when the Work Order was received.')
    )
)

DateAccepted = WorkflowDateField(
    'DateAccepted',
    readonly=True,
    widget=ComputedWidget(
        label=_('Date Accepted'),
        description=_('The date the Work Order was accepted.')
    )
)

DateReleased = WorkflowDateField(
    'DateReleased',
    readonly=True,
    widget=ComputedWidget(
        label=_('Date Released'),
        description=_('Work Order released.')
    )
)

DatePrepared = WorkflowDateField(
    'DatePrepared',
    readonly=True,
    widget=ComputedWidget(
        label=_('Date Prepared'),
        description=_("The date this Work Order was prepared.")
    )
)

DateTested = WorkflowDateField(
    'DateTested',
    readonly=True,
    widget=ComputedWidget(
        label=_('Date Tested'),
        description=_("The date this Work Order was flagged tested.")
    )
)

DatePassedQA = WorkflowDateField(
    'DatePassedQA',
    readonly=True,
    widget=ComputedWidget(
        label=_('Date Passed QA'),
        description=_('The Work Order QA Passed.')
    )
)

DatePublished = WorkflowDateField(
    'DatePublished',
    widget=ComputedWidget(
        label=_('Date Published'),
        description=_('The Work Order last last published.')
    )
)

DateCancelled = WorkflowDateField(
    'DateCancelled',
    widget=ComputedWidget(
        label=_('Date Cancelled'),
        description=_(
            'Contains a date, if the Work Order has been cancelled.')
    )
)

DateOfRetractions = RetractionDatesField(
    'DateOfRetractions',
    widget=LinesWidget(
        label=_('Date Of AR Retractions'),
        description=_(
            'Show retraction dates for all ARs inside this Work Order. Each '
            'line contains AR ID, Analysis ID, username, and a timestamp.'),
        size=10,
        mode='r',
    )
)

DateQADue = ExtDateTimeField(
    'DateQADue',
    widget=DateTimeWidget(
        label=_('Date QA Due'),
        description=_("Date when QA should be due"))
)

DatePublicationDue = ExtDateTimeField(
    'DatePublicationDue',
    widget=DateTimeWidget(
        label=_('Date Publications Due'),
        description=_("Date when Publication should be due"))
)

ActivitySampled = ExtStringField(
    'ActivitySampled',
    required=False,
    # This is not true, but required to legitimise the schemata.
    widget=StringWidget(
        label=_('Activity Sampled'),
        visible={'view': 'visible',
                 'edit': 'visible'}
    ),
)

QCBlanksProvided = ExtBooleanField(
    'QCBlanksProvided',
    required=False,
    # This is not true, but required to legitimise the schemata.
    widget=BooleanWidget(
        label=_('QC Blanks Provided'),
        visible={'view': 'visible',
                 'edit': 'visible'}
    ),
)

MediaLotNr = ExtStringField(
    'MediaLotNr',
    required=False,
    # This is not true, but required to legitimise the schemata.
    widget=StringWidget(
        label=_('Media Lot Number'),
        visible={'view': 'visible',
                 'edit': 'visible'}
    ),
)

SampleAndQCLotMatch = ExtBooleanField(
    'SampleAndQCLotMatch',
    required=False,
    widget=BooleanWidget(
        label=_('Lot for samples matches QC Blanks'),
        visible={'view': 'visible',
                 'edit': 'visible'}
    ),
)

MSDSorSDS = ExtBooleanField(
    'MSDSorSDS',
    required=False,
    widget=BooleanWidget(
        label=_('MSDS or SDS provided'),
        visible={'view': 'visible',
                 'edit': 'visible'}
    ),
)

ClientSampleComment = ExtTextField(
    'ClientSampleComment',
    default_content_type='text/x-web-intelligent',
    allowable_content_types=('text/plain',),
    default_output_type="text/plain",
    widget=TextAreaWidget(
        label=_('Client Sample Comment'),
    )
)

ExceptionalHazards = ExtTextField(
    'ExceptionalHazards',
    default_content_type='text/x-web-intelligent',
    allowable_content_types=('text/plain',),
    default_output_type="text/plain",
    widget=TextAreaWidget(
        label=_('Exceptional hazards'),
        description=_(
            "The value selected here will be set as the default for new Samples."),
    )
)

AmountSampled = ExtStringField(
    'AmountSampled',
    required=False,
    widget=StringWidget(
        label=_('Amount Sampled'),
        visible={'view': 'visible',
                 'edit': 'visible'}
    ),
)

AmountSampledMetric = ExtStringField(
    'AmountSampledMetric',
    required=False,
    widget=StringWidget(
        label=_('Amount Sampled Metric'),
        visible={'view': 'visible',
                 'edit': 'visible'}
    ),
)

ApprovedExceptionsToStandardPractice = ExtTextField(
    'ApprovedExceptionsToStandardPractice',
    required=False,
    widget=TextAreaWidget(
        label=_('Approved Exceptions To Standard Practice'),
        visible={'view': 'visible',
                 'edit': 'visible'}
    ),
)

NonStandardMethodInstructions = ExtTextField(
    'NonStandardMethodInstructions',
    required=False,
    widget=TextAreaWidget(
        label=_('Non-standard Method Instructions'),
        visible={'view': 'visible',
                 'edit': 'visible'}
    ),
)


class BatchSchemaExtender(object):
    adapts(IBatch)
    implements(IOrderableSchemaExtender)

    fields = [
        Contact,
        CCContact,
        CCEmails,
        InvoiceContact,
        Analysts,
        LeadAnalyst,
        ClientProjectName,
        SampleSource,
        SampleSite,
        SampleType,
        SampleMatrix,
        Profile,
        Container,
        ClientPONumber,
        ClientBatchComment,
        DateSampled,
        StorageLocation,
        ReturnSampleToClient,
        SampleTemperature,
        SampleCondition,
        BioHazardous,
        Methods,
        DateApproved,
        DateReceived,
        DateAccepted,
        DateReleased,
        DatePrepared,
        DateTested,
        DatePassedQA,
        DatePublished,
        DateCancelled,
        DateOfRetractions,
        DateQADue,
        DatePublicationDue,
        ActivitySampled,
        QCBlanksProvided,
        MediaLotNr,
        SampleAndQCLotMatch,
        MSDSorSDS,
        ClientSampleComment,
        ExceptionalHazards,
        AmountSampled,
        AmountSampledMetric,
        ApprovedExceptionsToStandardPractice,
        NonStandardMethodInstructions,
    ]

    def __init__(self, context):
        self.context = context

    def getOrder(self, schematas):
        """Return modified order of field schematas.
        """

        schematas["Create and Approve"] = [
            "title",
            "Client",
            "description",
            "DateSampled",
            "BatchDate",
            "BatchLabels",
            "ClientProjectName",
            "ClientBatchID",
            "Contact",
            "CCContact",
            "CCEmails",
            "InvoiceContact",
            "ClientBatchComment",
            "ClientPONumber",
            "ReturnSampleToClient",
            "SampleSite",
            "SampleSource",
            "SampleType",
            "SampleMatrix",
            "Remarks",
            "InheritedObjects",
            "InheritedObjectsUI",
        ]
        schematas["Receive and Accept"] = [
            "StorageLocation",
            ## "ReturnSampleToClient",
            "SampleTemperature",
            "SampleCondition",
            ## "SampleType",
            ## "SampleMatrix",
            "Container",
            "ActivitySampled",
            "MediaLotNr",
            "QCBlanksProvided",
            "MSDSorSDS",
            "SampleAndQCLotMatch",
            "ClientSampleComment",
            "BioHazardous",
            "ExceptionalHazards",
            "AmountSampled",
            "AmountSampledMetric",
        ]
        schematas["Assign"] = [
            "Analysts",
            "LeadAnalyst",
            "Methods",
            "Profile",
            "NonStandardMethodInstructions",
            "ApprovedExceptionsToStandardPractice",
        ]
        schematas["Dates"] = [
            ## "DateSampled",
            "DateQADue",
            "DatePublicationDue",
            "DateApproved",
            "DateReceived",
            "DateAccepted",
            "DateReleased",
            "DatePrepared",
            "DateTested",
            "DatePassedQA",
            "DatePublished",
            "DateCancelled",
            "DateOfRetractions",
        ]

        return schematas

    def getFields(self):
        return self.fields


class BatchSchemaModifier(object):
    adapts(IBatch)
    implements(ISchemaModifier)

    def __init__(self, context):
        self.context = context

    def hide_fields(self, schema, fieldnames):
        """Hide fields UW doesn't care to see
        """
        for fn in fieldnames:
            if fn in schema:
                schema[fn].widget.visible = {"view": "invisible",
                                             "edit": "invisible"}

    def get_client(self, schema, fieldnames):
        """All Client Contact fields must be restricted to show only relevant
        Contacts.  During creation the batch can be in some weird states
        and is located inside some odd contexs (TempFolder, PortalFactory),
        so some wiggling required.  We also can't use schema field accessors
        directly, as it causes recursion.
        """
        client = None
        # If heirarchy does not exist we're in early creation; skip body.
        if hasattr(self, 'context') and hasattr(self.context, 'aq_parent'):
            parent = self.context.aq_parent
            while not IPloneSiteRoot.providedBy(parent):
                if IClient.providedBy(parent):
                    client = parent
                    break
                parent = parent.aq_parent
        return client

    def filter_client_lookups(self, schema, client):
        if IClient.providedBy(client):
            ids = [c.getId() for c in client.objectValues('Contact')]
            for fn in ["Contact", "CCContact", "InvoiceContact"]:
                if fn in schema:
                    schema[fn].widget.base_query['id'] = ids

    def fiddle(self, schema):
        """
        """

        self.hide_fields(schema, ["Client",
                                  "BatchDate",
                                  "InheritedObjectsUI",
                                  "Remarks",
                                  "title"])

        client = self.get_client(self, schema)
        if client:
            self.filter_client_lookups(schema, client)

        return schema
