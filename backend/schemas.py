from pydantic import BaseModel
from typing import Optional
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
    linkedin_connected: bool = False

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

class ContactResponse(BaseModel):
    id: int
    name: str
    company: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    city: Optional[str]
    score: Optional[int]
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
    message: str

class WhatsAppSendResponse(BaseModel):
    configured: bool
    message: str

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

# Token
class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str
    role: str
