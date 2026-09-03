from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# User Schemas
class UserLogin(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: str
    role: str = "employee"

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True

# Lead Schemas
class LeadCreate(BaseModel):
    name: str
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    product: Optional[str] = None
    source: Optional[str] = None

class LeadUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    product: Optional[str] = None
    status: Optional[str] = None
    ai_score: Optional[int] = None
    lead_tier: Optional[str] = None

class LeadAssign(BaseModel):
    team_member_id: Optional[int] = None  # None unassigns the lead

class LeadResponse(BaseModel):
    id: int
    name: str
    company: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    product: Optional[str]
    ai_score: Optional[int]
    lead_tier: Optional[str]
    status: str
    source: Optional[str]
    created_at: datetime
    updated_at: datetime
    assigned_team_member_id: Optional[int] = None
    assigned_team_member_name: Optional[str] = None
    converted_contact_id: Optional[int] = None
    converted_contact_name: Optional[str] = None
    call_id: Optional[int] = None
    call_name: Optional[str] = None
    task_id: Optional[int] = None
    task_name: Optional[str] = None
    deal_id: Optional[int] = None
    deal_label: Optional[str] = None
    company_id: Optional[int] = None
    company_name: Optional[str] = None
    quotation_id: Optional[int] = None
    quotation_title: Optional[str] = None
    contact_id: Optional[int] = None  # a related Contact this lead is linked to - distinct
    contact_name: Optional[str] = None  # from converted_contact_id, the conversion result

# Deal Schemas
class DealCreate(BaseModel):
    lead_id: int
    deal_value: float
    probability: float = 0.5
    loan_product: str = "LAP"  # LAP, OD, CC, Home, Business, Project
    stage: Optional[str] = None  # new, qualified, proposal, negotiation, closed - defaults to 'new'
    company_id: Optional[int] = None  # linked Companies record

class DealMove(BaseModel):
    stage: str  # new, qualified, proposal, negotiation, closed

class DealAssign(BaseModel):
    team_member_id: Optional[int] = None  # None unassigns the deal

class DealCompanyAssign(BaseModel):
    company_id: Optional[int] = None  # None unlinks the deal from any Company record

class DealContactAssign(BaseModel):
    contact_id: Optional[int] = None  # None unlinks the deal from any Contact

class QuotationContactAssign(BaseModel):
    contact_id: Optional[int] = None  # None unlinks the quotation from any Contact

class QuotationCompanyAssign(BaseModel):
    company_id: Optional[int] = None  # None unlinks the quotation from any Company

class CallContactAssign(BaseModel):
    contact_id: Optional[int] = None  # None unlinks the call from any Contact

class CallCompanyAssign(BaseModel):
    company_id: Optional[int] = None  # None unlinks the call from any Company

class TaskContactAssign(BaseModel):
    contact_id: Optional[int] = None  # None unlinks the task from any Contact

class TaskCompanyAssign(BaseModel):
    company_id: Optional[int] = None  # None unlinks the task from any Company

class MeetingCompanyAssign(BaseModel):
    company_id: Optional[int] = None  # None unlinks the meeting from any Company

class MeetingDealAssign(BaseModel):
    deal_id: Optional[int] = None  # None unlinks the meeting from any Deal

class MeetingCallAssign(BaseModel):
    call_id: Optional[int] = None  # None unlinks the meeting from any Call

class MeetingTaskAssign(BaseModel):
    task_id: Optional[int] = None  # None unlinks the meeting from any Task

class MeetingQuotationAssign(BaseModel):
    quotation_id: Optional[int] = None  # None unlinks the meeting from any Quotation

class LeadCallAssign(BaseModel):
    call_id: Optional[int] = None  # None unlinks the lead from any Call

class LeadTaskAssign(BaseModel):
    task_id: Optional[int] = None  # None unlinks the lead from any Task

class LeadDealAssign(BaseModel):
    deal_id: Optional[int] = None  # None unlinks the lead from any Deal

class LeadCompanyAssign(BaseModel):
    company_id: Optional[int] = None  # None unlinks the lead from any Company

class LeadQuotationAssign(BaseModel):
    quotation_id: Optional[int] = None  # None unlinks the lead from any Quotation

class LeadContactAssign(BaseModel):
    contact_id: Optional[int] = None  # None unlinks the lead from any Contact - distinct
    # from the one-time "Convert Lead to Contact" flow (leads.converted_contact_id): this is
    # an ordinary reference to an existing Contact (e.g. a referral), not a conversion result.

class DealCallAssign(BaseModel):
    call_id: Optional[int] = None  # None unlinks the deal from any Call

class DealTaskAssign(BaseModel):
    task_id: Optional[int] = None  # None unlinks the deal from any Task

class TaskCallAssign(BaseModel):
    call_id: Optional[int] = None  # None unlinks the task from any Call

class TaskQuotationAssign(BaseModel):
    quotation_id: Optional[int] = None  # None unlinks the task from any Quotation

class QuotationCallAssign(BaseModel):
    call_id: Optional[int] = None  # None unlinks the quotation from any Call

class QuotationDealAssign(BaseModel):
    deal_id: Optional[int] = None  # None unlinks the quotation from any Deal

class ContactCompanyAssign(BaseModel):
    company_id: Optional[int] = None  # None unlinks the contact from any Company

class DealProcessStatusUpdate(BaseModel):
    process_status: str  # Login, Sanction, Hold, Disbursed

class DealResponse(BaseModel):
    id: int
    lead_id: int
    deal_value: float
    stage: str
    probability: float
    loan_product: str
    expected_close_date: Optional[datetime]
    created_at: datetime
    assigned_team_member_id: Optional[int] = None
    assigned_team_member_name: Optional[str] = None
    process_status: str = "Login"
    quotation_count: int = 0
    company_id: Optional[int] = None
    company_name: Optional[str] = None
    contact_id: Optional[int] = None
    contact_name: Optional[str] = None
    call_id: Optional[int] = None
    call_name: Optional[str] = None
    task_id: Optional[int] = None
    task_name: Optional[str] = None

# Campaign Schemas
class CampaignCreate(BaseModel):
    name: str
    type: str = "Email"
    status: str = "Active"
    recipients: int = 0
    message: Optional[str] = None  # actual content sent to linked recipients

class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    recipients: Optional[int] = None
    opens: Optional[int] = None
    clicks: Optional[int] = None
    message: Optional[str] = None

class CampaignResponse(BaseModel):
    id: int
    name: str
    type: str
    status: str
    recipients: int
    opens: int
    clicks: int
    message: Optional[str] = None
    engagement: int
    progress: int
    linked_recipient_count: int = 0  # real Leads/Contacts added via campaign_recipients
    sent_count: int = 0
    created_at: datetime
    updated_at: datetime

# Campaign Recipients (Marketing <-> Leads/Contacts linking) - real people a campaign is
# actually aimed at, replacing the plain `recipients` number with real records.
class CampaignRecipientAdd(BaseModel):
    lead_ids: Optional[List[int]] = None
    contact_ids: Optional[List[int]] = None

class CampaignRecipientResponse(BaseModel):
    id: int
    campaign_id: int
    lead_id: Optional[int] = None
    lead_name: Optional[str] = None
    contact_id: Optional[int] = None
    contact_name: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    status: str  # Pending, Sent, Failed
    sent_at: Optional[datetime] = None
    added_at: datetime

class CampaignSendResult(BaseModel):
    sent: int
    failed: int
    skipped: int
    message: str

# Integration Schemas
class IntegrationToggle(BaseModel):
    connected: bool

class IntegrationResponse(BaseModel):
    id: int
    name: str
    logo: Optional[str]
    description: Optional[str]
    connected: bool
    last_sync: str

class IntegrationStatusItem(BaseModel):
    configured: bool
    detail: Optional[str] = None  # e.g. the connected Google/LinkedIn account, if relevant

# Settings Schemas
class SettingsUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    timezone: Optional[str] = None
    theme: Optional[str] = None
    notifications: Optional[bool] = None
    email_notifications: Optional[bool] = None
    sms_notifications: Optional[bool] = None
    ga_tracking_id: Optional[str] = None
    default_report_period: Optional[str] = None

class SettingsResponse(BaseModel):
    full_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    company: Optional[str]
    timezone: str
    theme: str
    notifications: bool
    email_notifications: bool
    sms_notifications: bool
    ga_tracking_id: Optional[str] = None
    default_report_period: Optional[str] = None
    linkedin_connected: bool = False

# Contact Schemas
class ContactCreate(BaseModel):
    name: str
    company: Optional[str] = None
    company_id: Optional[int] = None  # linked Companies record, distinct from the free-text `company` field
    email: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    amount: Optional[float] = None
    bank: Optional[str] = None
    status: Optional[str] = None
    renewal_date: Optional[str] = None  # ISO "YYYY-MM-DD" - when their policy/loan is next due

class ContactUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    company_id: Optional[int] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    score: Optional[int] = None
    amount: Optional[float] = None
    bank: Optional[str] = None
    status: Optional[str] = None
    renewal_date: Optional[str] = None

class ContactAssign(BaseModel):
    team_member_id: Optional[int] = None  # None unassigns the contact

class ContactCompanyAssign(BaseModel):
    company_id: Optional[int] = None  # None unlinks the contact from any Company record

class ContactQuotationAssign(BaseModel):
    quotation_id: Optional[int] = None  # None unlinks the contact from any Quotation

class ContactCallAssign(BaseModel):
    call_id: Optional[int] = None  # None unlinks the contact from any Call

class ContactResponse(BaseModel):
    id: int
    name: str
    company: Optional[str]
    company_id: Optional[int] = None
    company_name: Optional[str] = None
    email: Optional[str]
    phone: Optional[str]
    city: Optional[str]
    score: Optional[int]
    amount: Optional[float] = None
    bank: Optional[str] = None
    status: Optional[str] = None
    renewal_date: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    assigned_team_member_id: Optional[int] = None
    assigned_team_member_name: Optional[str] = None
    converted_from_lead_id: Optional[int] = None
    converted_from_lead_name: Optional[str] = None
    quotation_id: Optional[int] = None
    quotation_title: Optional[str] = None
    call_id: Optional[int] = None
    call_name: Optional[str] = None

# Renewal Reminders (Dashboard "Upcoming Renewals" widget)
class RenewalContact(BaseModel):
    id: int
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    bank: Optional[str] = None
    amount: Optional[float] = None
    renewal_date: str
    days_until_renewal: int
    urgency: str  # "overdue", "due_soon" (<=7 days), "upcoming" (<=30 days)
    assigned_team_member_name: Optional[str] = None

# Contact Note Schemas
class ContactNoteCreate(BaseModel):
    call_datetime: Optional[str] = None
    next_conversation: Optional[str] = None
    transcript: str

class ContactNoteUpdate(BaseModel):
    call_datetime: Optional[str] = None
    next_conversation: Optional[str] = None
    transcript: Optional[str] = None

class ContactNoteResponse(BaseModel):
    id: int
    contact_id: int
    call_datetime: Optional[str]
    next_conversation: Optional[str]
    transcript: Optional[str]
    audio_url: Optional[str]
    created_at: datetime
    updated_at: datetime

# Lead Note Schemas
class LeadNoteCreate(BaseModel):
    call_datetime: Optional[str] = None
    next_conversation: Optional[str] = None
    transcript: str

class LeadNoteUpdate(BaseModel):
    call_datetime: Optional[str] = None
    next_conversation: Optional[str] = None
    transcript: Optional[str] = None

class LeadNoteResponse(BaseModel):
    id: int
    lead_id: int
    call_datetime: Optional[str]
    next_conversation: Optional[str]
    transcript: Optional[str]
    audio_url: Optional[str]
    created_at: datetime
    updated_at: datetime

# Task Schemas (Today page)
class TaskCreate(BaseModel):
    title: str
    due_date: str  # ISO "YYYY-MM-DD"
    priority: Optional[str] = None  # Low, Normal, High
    assigned_team_member_id: Optional[int] = None
    lead_id: Optional[int] = None
    contact_id: Optional[int] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    due_date: Optional[str] = None
    completed: Optional[bool] = None
    priority: Optional[str] = None
    assigned_team_member_id: Optional[int] = None
    lead_id: Optional[int] = None
    contact_id: Optional[int] = None

class TaskResponse(BaseModel):
    id: int
    title: str
    due_date: str
    completed: bool
    priority: str = "Normal"
    assigned_team_member_id: Optional[int] = None
    assigned_team_member_name: Optional[str] = None
    lead_id: Optional[int] = None
    lead_name: Optional[str] = None
    contact_id: Optional[int] = None
    contact_name: Optional[str] = None
    call_id: Optional[int] = None
    call_name: Optional[str] = None
    quotation_id: Optional[int] = None
    quotation_title: Optional[str] = None
    company_id: Optional[int] = None
    company_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# Meeting Schemas (Today page)
class MeetingCreate(BaseModel):
    title: str
    meeting_date: str  # ISO "YYYY-MM-DD"
    meeting_time: Optional[str] = None  # "HH:MM"
    lead_id: Optional[int] = None
    contact_id: Optional[int] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    assigned_team_member_id: Optional[int] = None

class MeetingUpdate(BaseModel):
    title: Optional[str] = None
    meeting_date: Optional[str] = None
    meeting_time: Optional[str] = None
    lead_id: Optional[int] = None
    contact_id: Optional[int] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None  # Scheduled, Conducted, Cancelled
    assigned_team_member_id: Optional[int] = None

class MeetingResponse(BaseModel):
    id: int
    title: str
    meeting_date: str
    meeting_time: Optional[str] = None
    lead_id: Optional[int] = None
    lead_name: Optional[str] = None
    contact_id: Optional[int] = None
    contact_name: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    status: str = "Scheduled"
    assigned_team_member_id: Optional[int] = None
    assigned_team_member_name: Optional[str] = None
    company_id: Optional[int] = None
    company_name: Optional[str] = None
    deal_id: Optional[int] = None
    deal_label: Optional[str] = None
    call_id: Optional[int] = None
    call_name: Optional[str] = None
    task_id: Optional[int] = None
    task_name: Optional[str] = None
    quotation_id: Optional[int] = None
    quotation_title: Optional[str] = None
    google_calendar_event_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# Call Schemas
class CallCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    duration_seconds: int = 0
    type: str = "Outbound"
    outcome: Optional[str] = None
    call_date: Optional[str] = None
    team_member_id: Optional[int] = None
    lead_id: Optional[int] = None
    contact_id: Optional[int] = None

class CallAssign(BaseModel):
    team_member_id: Optional[int] = None  # None unassigns the call

class CallResponse(BaseModel):
    id: int
    name: str
    phone: Optional[str]
    duration_seconds: int
    duration: str
    type: str
    outcome: Optional[str]
    call_date: Optional[str]
    created_at: datetime
    team_member_id: Optional[int] = None
    team_member_name: Optional[str] = None
    lead_id: Optional[int] = None
    lead_name: Optional[str] = None
    contact_id: Optional[int] = None
    contact_name: Optional[str] = None
    company_id: Optional[int] = None
    company_name: Optional[str] = None
    recording_url: Optional[str] = None

# Communication Log (Emails/WhatsApp/SMS actually sent - "Emails"/"WhatsApp" tabs alongside
# Calls, matching how Kylas groups Call Logs/Emails/WhatsApp under one nav item)
class CommunicationLogResponse(BaseModel):
    id: int
    channel: str  # Email, WhatsApp, SMS
    recipient: Optional[str] = None
    subject: Optional[str] = None
    message: Optional[str] = None
    status: str  # Sent, Failed
    error_detail: Optional[str] = None
    created_at: datetime
    lead_id: Optional[int] = None
    lead_name: Optional[str] = None
    contact_id: Optional[int] = None
    contact_name: Optional[str] = None

# Per-employee call attempt/connect counts, for admins and team leads
class EmployeeCallStats(BaseModel):
    team_member_id: int
    name: str
    today_attempted: int
    today_connected: int
    week_attempted: int
    week_connected: int
    month_attempted: int
    month_connected: int

# Twilio click-to-call
class DialRequest(BaseModel):
    to: str  # customer's phone number to connect the agent to
    lead_id: Optional[int] = None
    contact_id: Optional[int] = None

class DialResponse(BaseModel):
    configured: bool
    message: str
    call_sid: Optional[str] = None
    call_id: Optional[int] = None  # the auto-logged calls.id, if a real call was placed

# Claude AI note assistant
class AISummaryResponse(BaseModel):
    configured: bool
    message: str
    suggestion: Optional[str] = None

# Claude AI follow-up date detection (Notes modal - "did you mention a date in that note?")
class DetectDateRequest(BaseModel):
    text: str

class DetectDateResponse(BaseModel):
    configured: bool
    message: str
    detected_date: Optional[str] = None  # ISO "YYYY-MM-DDTHH:MM" if a date/time was found

# CRM chatbot (floating "Ask AI" widget, every page)
class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[list[ChatMessage]] = None

class ChatResponse(BaseModel):
    configured: bool
    message: str
    reply: Optional[str] = None

# Claude AI marketing content generation (Marketing tab - AI Content Studio)
class GenerateContentRequest(BaseModel):
    occasion: str  # e.g. "Diwali", "Policy Renewal Reminder", or free text
    platform: str = "WhatsApp"  # WhatsApp, Email, LinkedIn, SMS
    notes: Optional[str] = None  # extra context from the user, e.g. product to promote

class GenerateContentResponse(BaseModel):
    configured: bool
    message: str
    content: Optional[str] = None

# WhatsApp Business API (Meta Cloud API)
class WhatsAppSendRequest(BaseModel):
    to: str
    message: Optional[str] = None  # freeform text - required unless template_name is set
    template_name: Optional[str] = None
    template_language: Optional[str] = "en_US"
    template_params: Optional[List[str]] = None  # values for the template's {{1}}, {{2}}, ... body variables
    lead_id: Optional[int] = None
    contact_id: Optional[int] = None

class WhatsAppSendResponse(BaseModel):
    configured: bool
    message: str
    conversation_id: Optional[int] = None

class WhatsAppReplyRequest(BaseModel):
    message: Optional[str] = None
    template_name: Optional[str] = None
    template_language: Optional[str] = "en_US"
    template_params: Optional[List[str]] = None

class WhatsAppTemplatesResponse(BaseModel):
    configured: bool
    message: str
    templates: List[dict] = []

class WhatsAppConversationResponse(BaseModel):
    id: int
    contact_id: Optional[int]
    lead_id: Optional[int]
    contact_name: Optional[str] = None
    lead_name: Optional[str] = None
    wa_number: str
    status: str
    assigned_user_id: Optional[int] = None
    opted_out_at: Optional[str] = None
    opt_out_reason: Optional[str] = None
    last_message_at: Optional[str] = None
    last_message: Optional[str] = None
    last_message_type: Optional[str] = None
    created_at: datetime

class WhatsAppMessageResponse(BaseModel):
    id: int
    conversation_id: int
    direction: str
    wa_message_id: Optional[str]
    message_type: str
    template_name: Optional[str]
    body: Optional[str]
    media_url: Optional[str]
    status: str
    error_message: Optional[str]
    created_by: Optional[int]
    created_at: datetime

class ConversationAssign(BaseModel):
    user_id: Optional[int] = None  # None unassigns

class ConversationStatusUpdate(BaseModel):
    status: str  # open, closed, handed_off

# WhatsApp Flows (Meta's native in-chat forms - loan applications, KYC checklists, bookings)
class FlowCreate(BaseModel):
    meta_flow_id: str
    name: str
    status: str = "draft"  # draft, published - mirrors the Flow's real status in Meta Business Manager
    terminal_screen: str = "SUCCESS"

class FlowUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    terminal_screen: Optional[str] = None

class FlowResponse(BaseModel):
    id: int
    meta_flow_id: str
    name: str
    status: str
    terminal_screen: str
    created_at: datetime

class FlowSendRequest(BaseModel):
    to: str
    header_text: Optional[str] = None
    body_text: str
    footer_text: Optional[str] = None
    cta_text: str = "Start"
    screen: Optional[str] = None  # the Flow's first screen id - required by Meta
    initial_data: Optional[dict] = None  # pre-fills fields on that first screen
    lead_id: Optional[int] = None
    contact_id: Optional[int] = None

class FlowSendResponse(BaseModel):
    configured: bool
    message: str
    flow_token: Optional[str] = None
    conversation_id: Optional[int] = None

class FlowSessionResponse(BaseModel):
    id: int
    flow_token: str
    flow_id: int
    conversation_id: Optional[int]
    current_screen: Optional[str]
    status: str
    submission_json: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

# Email Service (SMTP)
class EmailSendRequest(BaseModel):
    to: str
    subject: str
    body: str
    lead_id: Optional[int] = None
    contact_id: Optional[int] = None

class EmailSendResponse(BaseModel):
    configured: bool
    message: str

# SMS (Twilio)
class SmsSendRequest(BaseModel):
    to: str
    message: str
    lead_id: Optional[int] = None
    contact_id: Optional[int] = None

class SmsSendResponse(BaseModel):
    configured: bool
    message: str

# Mailchimp sync (Marketing)
class MailchimpSyncResponse(BaseModel):
    configured: bool
    message: str
    synced_count: Optional[int] = None

# LinkedIn (Marketing tab "Post to LinkedIn")
class LinkedInConnectResponse(BaseModel):
    configured: bool
    message: str
    auth_url: Optional[str] = None

class LinkedInPostRequest(BaseModel):
    text: str

class LinkedInPostResponse(BaseModel):
    configured: bool
    message: str
    post_urn: Optional[str] = None

# Google Sheets sync (export contacts/leads out, or bulk-import leads in)
class GoogleConnectResponse(BaseModel):
    configured: bool
    message: str
    auth_url: Optional[str] = None

class GoogleStatusResponse(BaseModel):
    connected: bool
    google_email: Optional[str] = None

class GoogleSheetsExportRequest(BaseModel):
    spreadsheet_id: str  # the id from the sheet's URL (.../spreadsheets/d/<THIS>/edit)
    sheet_name: str = "Sheet1"
    entity: str  # "contacts" or "leads"

class GoogleSheetsExportResponse(BaseModel):
    configured: bool
    message: str
    rows_written: int = 0

class GoogleSheetsImportRequest(BaseModel):
    spreadsheet_id: str
    sheet_name: str = "Sheet1"

class GoogleSheetsImportResponse(BaseModel):
    configured: bool
    message: str
    created: int = 0
    failed: int = 0

# Gmail (send-only, via the same connected Google account as Google Sheets)
class GmailSendRequest(BaseModel):
    to: str
    subject: str
    body: str
    lead_id: Optional[int] = None
    contact_id: Optional[int] = None

class GmailSendResponse(BaseModel):
    configured: bool
    message: str

# Google Calendar (same connected Google account) - syncs a CRM Meeting to a real event
class CalendarSyncResponse(BaseModel):
    configured: bool
    message: str
    event_link: Optional[str] = None

# Zapier outbound webhooks - no OAuth, just a "Catch Hook" URL the CRM POSTs to on events
class ZapierWebhookCreate(BaseModel):
    url: str
    event_type: str = "all"  # 'lead.created', 'deal.closed', or 'all'

class ZapierWebhookResponse(BaseModel):
    id: int
    url: str
    event_type: str
    created_at: datetime
    last_triggered_at: Optional[str] = None
    last_status: Optional[str] = None

# Slack outbound notifications - same shape as Zapier's webhooks, but POSTs a formatted
# {"text": "..."} message (Slack's Incoming Webhook format) instead of a raw event dump
class SlackWebhookCreate(BaseModel):
    url: str
    event_type: str = "all"  # 'lead.created', 'deal.closed', or 'all'

class SlackWebhookResponse(BaseModel):
    id: int
    url: str
    event_type: str
    created_at: datetime
    last_triggered_at: Optional[str] = None
    last_status: Optional[str] = None

# Priti - AI Voice Caller (Vapi)
class VoiceCallTriggerRequest(BaseModel):
    lead_id: Optional[int] = None
    contact_id: Optional[int] = None
    reason: str  # why Priti is calling this person - must be true, read out on the call

class VoiceCallTriggerResponse(BaseModel):
    configured: bool
    message: str
    vapi_call_id: Optional[str] = None

# Team Management
class TeamMemberCreate(BaseModel):
    name: str
    role: str  # admin, team_lead, location_head, employee
    email: Optional[str] = None
    phone: Optional[str] = None

class TeamMemberUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

class TeamMemberResponse(BaseModel):
    id: int
    name: str
    role: str
    email: Optional[str]
    phone: Optional[str]
    created_at: datetime

class TeamProductivityRow(BaseModel):
    id: int
    name: str
    role: str
    calls: Optional[int] = None
    deals_closed: Optional[int] = None
    revenue: Optional[float] = None
    conversion_rate: Optional[float] = None
    tasks_completed: Optional[int] = None
    meetings_conducted: Optional[int] = None

# Call Dialer (Kylas "My Call Dialer" parity) - a work queue: leads/contacts assigned to a
# team member to dial through in sequence, tracked separately from the calls actually logged.
class DialerAssignRequest(BaseModel):
    team_member_id: int
    lead_ids: Optional[List[int]] = None
    contact_ids: Optional[List[int]] = None

class DialerQueueItemResponse(BaseModel):
    id: int
    lead_id: Optional[int] = None
    contact_id: Optional[int] = None
    name: str
    phone: Optional[str] = None
    team_member_id: int
    team_member_name: Optional[str] = None
    status: str  # Pending, Called, Skipped
    assigned_by: Optional[int] = None
    assigned_by_name: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

class DialerStatusUpdate(BaseModel):
    status: str  # Called, Skipped

# Unified Activities feed (Kylas "Campaigns > Activities" parity) - merges communication_log
# (Email/WhatsApp/SMS sends) and calls into one chronological timeline instead of three tabs.
class ActivityItem(BaseModel):
    id: str  # prefixed with source table so ids from calls/communication_log never collide
    channel: str  # Call, Email, WhatsApp, SMS, Task, Meeting, Campaign
    contact: Optional[str] = None
    detail: Optional[str] = None
    outcome: Optional[str] = None
    timestamp: datetime
    lead_id: Optional[int] = None
    lead_name: Optional[str] = None
    contact_id: Optional[int] = None
    contact_name: Optional[str] = None

# Companies (Kylas parity) - a lightweight standalone directory, not yet linked to Contacts;
# ArthaInvest works mostly with individuals, so this stays optional metadata for now.
class CompanyCreate(BaseModel):
    name: str
    industry: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    notes: Optional[str] = None

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    notes: Optional[str] = None

class CompanyResponse(BaseModel):
    id: int
    name: str
    industry: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    notes: Optional[str] = None
    contact_count: int = 0
    deal_count: int = 0
    quotation_count: int = 0
    created_at: datetime
    updated_at: datetime

# Quotations (Kylas parity) - a formal price quote linked to a Lead or Contact, with line
# items and a status lifecycle (Draft -> Sent -> Accepted/Rejected).
class QuotationItemInput(BaseModel):
    description: str
    amount: float

class QuotationItemResponse(BaseModel):
    id: int
    description: str
    amount: float

class QuotationCreate(BaseModel):
    lead_id: Optional[int] = None
    contact_id: Optional[int] = None
    deal_id: Optional[int] = None
    title: str
    valid_until: Optional[str] = None  # ISO "YYYY-MM-DD"
    notes: Optional[str] = None
    items: List[QuotationItemInput] = []

class QuotationUpdate(BaseModel):
    lead_id: Optional[int] = None
    contact_id: Optional[int] = None
    deal_id: Optional[int] = None
    title: Optional[str] = None
    valid_until: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None  # Draft, Sent, Accepted, Rejected
    items: Optional[List[QuotationItemInput]] = None  # when present, fully replaces existing items

class QuotationResponse(BaseModel):
    id: int
    quotation_number: str
    lead_id: Optional[int] = None
    lead_name: Optional[str] = None
    contact_id: Optional[int] = None
    contact_name: Optional[str] = None
    deal_id: Optional[int] = None
    deal_label: Optional[str] = None
    company_id: Optional[int] = None
    company_name: Optional[str] = None
    assigned_team_member_id: Optional[int] = None
    assigned_team_member_name: Optional[str] = None
    call_id: Optional[int] = None
    call_name: Optional[str] = None
    title: str
    status: str
    valid_until: Optional[str] = None
    notes: Optional[str] = None
    grand_total: float
    items: List[QuotationItemResponse] = []
    created_at: datetime
    updated_at: datetime

# Tags & Groups
class TagCreate(BaseModel):
    name: str
    color: Optional[str] = "#9c6b2e"

class TagResponse(BaseModel):
    id: int
    name: str
    color: str
    created_at: datetime

class EntityTagRequest(BaseModel):
    entity_type: str  # 'contact' or 'lead'
    entity_id: int
    tag_id: int

class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None

class GroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime

class EntityGroupRequest(BaseModel):
    entity_type: str
    entity_id: int
    group_id: int

# Custom fields
class CustomFieldCreate(BaseModel):
    name: str
    field_type: Optional[str] = "text"

class CustomFieldResponse(BaseModel):
    id: int
    name: str
    field_type: str
    created_at: datetime

class CustomFieldValueSet(BaseModel):
    entity_type: str
    entity_id: int
    custom_field_id: int
    value: Optional[str] = None

# Quick replies (canned responses - not yet wired to a conversation UI on this branch)
class QuickReplyCreate(BaseModel):
    shortcut: str
    message: str

class QuickReplyUpdate(BaseModel):
    shortcut: Optional[str] = None
    message: Optional[str] = None

class QuickReplyResponse(BaseModel):
    id: int
    shortcut: str
    message: str
    created_at: datetime

# Automations (drip sequences - a named flow of ordered steps, enrolled per lead/contact
# via the same entity_type/entity_id pointer tags/groups use, or in bulk via a group)
class AutomationStepInput(BaseModel):
    wait_minutes: int = 0
    message_type: str = "text"  # 'text' or 'template'
    template_name: Optional[str] = None
    body: Optional[str] = None

class AutomationCreate(BaseModel):
    name: str
    trigger_type: str = "manual"  # manual, new_lead, group_join
    group_id: Optional[int] = None
    steps: List[AutomationStepInput] = []

class AutomationUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None  # active, paused
    steps: Optional[List[AutomationStepInput]] = None

class AutomationStepResponse(BaseModel):
    id: int
    step_order: int
    wait_minutes: int
    message_type: str
    template_name: Optional[str]
    body: Optional[str]

class AutomationResponse(BaseModel):
    id: int
    name: str
    trigger_type: str
    group_id: Optional[int]
    status: str
    created_at: datetime
    steps: List[AutomationStepResponse] = []

class AutomationEnrollRequest(BaseModel):
    entity_type: str  # 'lead' or 'contact'
    entity_id: int

class AutomationEnrollmentResponse(BaseModel):
    id: int
    automation_id: int
    entity_type: str
    entity_id: int
    entity_name: Optional[str] = None
    current_step: int
    total_steps: int
    status: str
    next_run_at: Optional[datetime]
    created_at: datetime

# Token
class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str
    role: str

# Developer API keys - let an external system (a website contact form, a click-to-WhatsApp ad
# landing page, a Zapier/webhook integration) call POST /api/public/leads to create leads
# without a user login. Only the SHA-256 hash of the key is ever persisted (see main.py's
# get_user_from_api_key()) - the raw value is returned exactly once, at creation time.
class ApiKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

class ApiKeyResponse(BaseModel):
    id: int
    name: str
    key_prefix: str
    created_at: datetime
    last_used_at: Optional[str] = None
    revoked_at: Optional[str] = None

class ApiKeyCreateResponse(BaseModel):
    id: int
    name: str
    api_key: str  # the raw key - shown once, here, never retrievable again

# Body for POST /api/public/leads. Deliberately its own schema (not LeadCreate) with tight
# length limits on every field - this endpoint is authenticated by API key rather than a JWT,
# reachable by any external system that has a key, so it must not become a way to write
# arbitrary/oversized data into the leads table.
class PublicLeadCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    company: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    product: Optional[str] = Field(None, max_length=100)
    source: Optional[str] = Field(None, max_length=100)
