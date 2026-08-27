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
    marketing_opt_in: Optional[bool] = None

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
    marketing_opt_in: Optional[bool] = False
    created_at: datetime
    updated_at: datetime

# Deal Schemas
class DealCreate(BaseModel):
    lead_id: int
    deal_value: float
    probability: float = 0.5
    loan_product: str = "LAP"  # LAP, OD, CC, Home, Business, Project
    stage: Optional[str] = None  # new, qualified, proposal, negotiation, closed - defaults to 'new'

class DealMove(BaseModel):
    stage: str  # new, qualified, proposal, negotiation, closed

class DealResponse(BaseModel):
    id: int
    lead_id: int
    deal_value: float
    stage: str
    probability: float
    loan_product: str
    expected_close_date: Optional[datetime]
    created_at: datetime

# Campaign Schemas
class CampaignCreate(BaseModel):
    name: str
    type: str = "Email"
    status: str = "Active"
    recipients: int = 0

class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    recipients: Optional[int] = None
    opens: Optional[int] = None
    clicks: Optional[int] = None

class CampaignResponse(BaseModel):
    id: int
    name: str
    type: str
    status: str
    recipients: int
    opens: int
    clicks: int
    engagement: int
    progress: int
    created_at: datetime
    updated_at: datetime

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

# Contact Schemas
class ContactCreate(BaseModel):
    name: str
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None

class ContactUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    score: Optional[int] = None
    marketing_opt_in: Optional[bool] = None

class ContactResponse(BaseModel):
    id: int
    name: str
    company: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    city: Optional[str]
    score: Optional[int]
    marketing_opt_in: Optional[bool] = False
    created_at: datetime
    updated_at: datetime

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

# Call Schemas
class CallCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    duration_seconds: int = 0
    type: str = "Outbound"
    outcome: Optional[str] = None
    call_date: Optional[str] = None

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

# Twilio click-to-call
class DialRequest(BaseModel):
    to: str  # customer's phone number to connect the agent to

class DialResponse(BaseModel):
    configured: bool
    message: str
    call_sid: Optional[str] = None

# Claude AI note assistant
class AISummaryResponse(BaseModel):
    configured: bool
    message: str
    suggestion: Optional[str] = None

# WhatsApp Business API (Meta Cloud API)
class WhatsAppSendRequest(BaseModel):
    to: str
    message: Optional[str] = None  # freeform text - required unless template_name is set
    template_name: Optional[str] = None
    template_language: Optional[str] = "en_US"
    template_params: Optional[List[str]] = None  # values for the template's {{1}}, {{2}}, ... body variables
    contact_id: Optional[int] = None
    lead_id: Optional[int] = None

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

# Quick replies
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

# Automations (drip sequences / simple flows)
class AutomationStepInput(BaseModel):
    wait_minutes: int = 0
    message_type: str = "template"  # 'template' recommended - freeform text only works inside a 24h reply window
    template_name: Optional[str] = None
    body: Optional[str] = None

class AutomationCreate(BaseModel):
    name: str
    trigger_type: str = "manual"  # manual, new_conversation, group_join
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
    conversation_id: int

# Developer API keys
class ApiKeyCreate(BaseModel):
    name: str

class ApiKeyResponse(BaseModel):
    id: int
    name: str
    key_prefix: str
    created_at: datetime
    last_used_at: Optional[str]
    revoked_at: Optional[str]

class ApiKeyCreateResponse(BaseModel):
    id: int
    name: str
    api_key: str  # shown once, at creation time only

# Email Service (SMTP)
class EmailSendRequest(BaseModel):
    to: str
    subject: str
    body: str

class EmailSendResponse(BaseModel):
    configured: bool
    message: str

# SMS (Twilio)
class SmsSendRequest(BaseModel):
    to: str
    message: str

class SmsSendResponse(BaseModel):
    configured: bool
    message: str

# Mailchimp sync (Marketing)
class MailchimpSyncResponse(BaseModel):
    configured: bool
    message: str
    synced_count: Optional[int] = None

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

# Token
class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str
    role: str
