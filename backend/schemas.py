from pydantic import BaseModel
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

class TaskContactAssign(BaseModel):
    contact_id: Optional[int] = None  # None unlinks the task from any Contact

class LeadCallAssign(BaseModel):
    call_id: Optional[int] = None  # None unlinks the lead from any Call

class LeadTaskAssign(BaseModel):
    task_id: Optional[int] = None  # None unlinks the lead from any Task

class LeadDealAssign(BaseModel):
    deal_id: Optional[int] = None  # None unlinks the lead from any Deal

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
    message: str
    lead_id: Optional[int] = None
    contact_id: Optional[int] = None

class WhatsAppSendResponse(BaseModel):
    configured: bool
    message: str

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

# Token
class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str
    role: str
