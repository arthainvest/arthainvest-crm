import axios from 'axios';

export const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Login tokens expire after ACCESS_TOKEN_EXPIRE_MINUTES (30 min by default, see backend/auth.py)
// with no refresh mechanism. Without this, an expired token makes every write silently fail and
// each form shows its own generic "Error creating X" alert with no indication that the real
// cause is just a stale session - so the user has no way to know they need to log back in.
// This catches it once, in one place, for every request, and sends them to a fresh login instead.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    const url = error.config?.url || '';
    const isAuthEndpoint = url.includes('/api/auth/login') || url.includes('/api/auth/register');
    if (status === 401 && !isAuthEndpoint && localStorage.getItem('token')) {
      localStorage.clear();
      window.location.href = '/login?expired=1';
    }
    return Promise.reject(error);
  }
);

// Authentication
export const loginUser = async (username, password) => {
  const response = await api.post('/api/auth/login', { username, password });
  return response.data;
};

export const registerUser = async (userData) => {
  const response = await api.post('/api/auth/register', userData);
  return response.data;
};

// Leads
export const getLeads = async (token, status = null, { source, assignedTeamMemberId } = {}) => {
  const params = new URLSearchParams();
  if (token) params.append('token', token);
  if (status) params.append('status', status);
  if (source) params.append('source', source);
  if (assignedTeamMemberId) params.append('assigned_team_member_id', assignedTeamMemberId);

  const response = await api.get(`/api/leads?${params.toString()}`);
  return response.data;
};

export const getLead = async (id, token) => {
  const response = await api.get(`/api/leads/${id}?token=${token}`);
  return response.data;
};

export const createLead = async (token, leadData) => {
  const response = await api.post(`/api/leads?token=${token}`, leadData);
  return response.data;
};

export const updateLead = async (token, id, leadData) => {
  const response = await api.put(`/api/leads/${id}?token=${token}`, leadData);
  return response.data;
};

export const deleteLead = async (token, id) => {
  await api.delete(`/api/leads/${id}?token=${token}`);
};

export const assignLead = async (token, leadId, teamMemberId) => {
  const response = await api.put(`/api/leads/${leadId}/assign?token=${token}`, { team_member_id: teamMemberId });
  return response.data;
};

export const convertLeadToContact = async (token, leadId) => {
  const response = await api.post(`/api/leads/${leadId}/convert?token=${token}`);
  return response.data;
};

// Lead notes
export const getLeadNotes = async (token, leadId) => {
  const response = await api.get(`/api/leads/${leadId}/notes?token=${token}`);
  return response.data;
};

export const createLeadNote = async (token, leadId, noteData) => {
  const response = await api.post(`/api/leads/${leadId}/notes?token=${token}`, noteData);
  return response.data;
};

export const updateLeadNote = async (token, leadId, noteId, noteData) => {
  const response = await api.put(`/api/leads/${leadId}/notes/${noteId}?token=${token}`, noteData);
  return response.data;
};

export const deleteLeadNote = async (token, leadId, noteId) => {
  await api.delete(`/api/leads/${leadId}/notes/${noteId}?token=${token}`);
};

export const uploadLeadNoteAudio = async (token, leadId, noteId, audioBlob) => {
  const formData = new FormData();
  formData.append('audio', audioBlob, 'recording.webm');
  const response = await api.post(
    `/api/leads/${leadId}/notes/${noteId}/audio?token=${token}`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  );
  return response.data;
};

// Deals
export const getDeals = async (token, stage = null, { leadId, assignedTeamMemberId } = {}) => {
  const params = new URLSearchParams();
  if (token) params.append('token', token);
  if (stage) params.append('stage', stage);
  if (leadId) params.append('lead_id', leadId);
  if (assignedTeamMemberId) params.append('assigned_team_member_id', assignedTeamMemberId);

  const response = await api.get(`/api/deals?${params.toString()}`);
  return response.data;
};

export const createDeal = async (token, dealData) => {
  const response = await api.post(`/api/deals?token=${token}`, dealData);
  return response.data;
};

export const moveDeal = async (token, dealId, stage) => {
  const response = await api.put(`/api/deals/${dealId}/move?token=${token}`, { stage });
  return response.data;
};

export const assignDeal = async (token, dealId, teamMemberId) => {
  const response = await api.put(`/api/deals/${dealId}/assign?token=${token}`, { team_member_id: teamMemberId });
  return response.data;
};

export const updateDealProcessStatus = async (token, dealId, processStatus) => {
  const response = await api.put(`/api/deals/${dealId}/process-status?token=${token}`, { process_status: processStatus });
  return response.data;
};

// Analytics
export const getDashboardAnalytics = async (token) => {
  const response = await api.get(`/api/analytics/dashboard?token=${token}`);
  return response.data;
};

export const getLoanStageDeals = async (token, label) => {
  const response = await api.get(`/api/analytics/dashboard/loan-stage-deals?token=${token}&label=${encodeURIComponent(label)}`);
  return response.data;
};

export const getConversionRate = async (token) => {
  const response = await api.get(`/api/analytics/conversion-rate?token=${token}`);
  return response.data;
};

export const getSalesAnalytics = async (token) => {
  const response = await api.get(`/api/analytics/sales?token=${token}`);
  return response.data;
};

export const getLeadSourceROI = async (token) => {
  const response = await api.get(`/api/analytics/lead-sources?token=${token}`);
  return response.data;
};

// Campaigns
export const getCampaigns = async (token) => {
  const response = await api.get(`/api/campaigns?token=${token}`);
  return response.data;
};

export const createCampaign = async (token, campaignData) => {
  const response = await api.post(`/api/campaigns?token=${token}`, campaignData);
  return response.data;
};

export const updateCampaign = async (token, id, campaignData) => {
  const response = await api.put(`/api/campaigns/${id}?token=${token}`, campaignData);
  return response.data;
};

export const deleteCampaign = async (token, id) => {
  await api.delete(`/api/campaigns/${id}?token=${token}`);
};

// Campaign recipients (Marketing <-> Leads/Contacts linking)
export const getCampaignRecipients = async (token, campaignId) => {
  const response = await api.get(`/api/campaigns/${campaignId}/recipients?token=${token}`);
  return response.data;
};

export const addCampaignRecipients = async (token, campaignId, { leadIds, contactIds }) => {
  const response = await api.post(`/api/campaigns/${campaignId}/recipients?token=${token}`, {
    lead_ids: leadIds, contact_ids: contactIds,
  });
  return response.data;
};

export const removeCampaignRecipient = async (token, campaignId, recipientId) => {
  await api.delete(`/api/campaigns/${campaignId}/recipients/${recipientId}?token=${token}`);
};

export const sendCampaign = async (token, campaignId) => {
  const response = await api.post(`/api/campaigns/${campaignId}/send?token=${token}`);
  return response.data;
};

// Integrations
export const getIntegrations = async (token) => {
  const response = await api.get(`/api/integrations?token=${token}`);
  return response.data;
};

export const toggleIntegration = async (token, id, connected) => {
  const response = await api.put(`/api/integrations/${id}/toggle?token=${token}`, { connected });
  return response.data;
};

// True configured/connected state for the integrations that are genuinely real (not just a
// cosmetic DB toggle) - keyed by integration name, overriding just those rows' displayed status.
export const getIntegrationsStatus = async (token) => {
  const response = await api.get(`/api/integrations/status?token=${token}`);
  return response.data;
};

// Google Sheets (OAuth - same shape as LinkedIn's connect flow above)
export const getGoogleConnectUrl = async (token) => {
  const response = await api.get(`/api/integrations/google/connect?token=${token}`);
  return response.data;
};

export const disconnectGoogle = async (token) => {
  const response = await api.post(`/api/integrations/google/disconnect?token=${token}`);
  return response.data;
};

export const exportToGoogleSheets = async (token, spreadsheetId, sheetName, entity) => {
  const response = await api.post(`/api/integrations/google-sheets/export?token=${token}`, {
    spreadsheet_id: spreadsheetId, sheet_name: sheetName, entity
  });
  return response.data;
};

export const importFromGoogleSheets = async (token, spreadsheetId, sheetName) => {
  const response = await api.post(`/api/integrations/google-sheets/import?token=${token}`, {
    spreadsheet_id: spreadsheetId, sheet_name: sheetName
  });
  return response.data;
};

// Settings
export const getSettings = async (token) => {
  const response = await api.get(`/api/settings?token=${token}`);
  return response.data;
};

export const updateSettings = async (token, settingsData) => {
  const response = await api.put(`/api/settings?token=${token}`, settingsData);
  return response.data;
};

// Contacts
export const getContactsList = async (token, { assignedTeamMemberId } = {}) => {
  const params = new URLSearchParams({ token });
  if (assignedTeamMemberId) params.append('assigned_team_member_id', assignedTeamMemberId);
  const response = await api.get(`/api/contacts?${params.toString()}`);
  return response.data;
};

export const createContact = async (token, contactData) => {
  const response = await api.post(`/api/contacts?token=${token}`, contactData);
  return response.data;
};

export const updateContact = async (token, id, contactData) => {
  const response = await api.put(`/api/contacts/${id}?token=${token}`, contactData);
  return response.data;
};

export const deleteContact = async (token, id) => {
  await api.delete(`/api/contacts/${id}?token=${token}`);
};

export const assignContact = async (token, contactId, teamMemberId) => {
  const response = await api.put(`/api/contacts/${contactId}/assign?token=${token}`, { team_member_id: teamMemberId });
  return response.data;
};

export const getUpcomingRenewals = async (token) => {
  const response = await api.get(`/api/contacts/renewals?token=${token}`);
  return response.data;
};

// Contact notes
export const getContactNotes = async (token, contactId) => {
  const response = await api.get(`/api/contacts/${contactId}/notes?token=${token}`);
  return response.data;
};

export const createContactNote = async (token, contactId, noteData) => {
  const response = await api.post(`/api/contacts/${contactId}/notes?token=${token}`, noteData);
  return response.data;
};

export const updateContactNote = async (token, contactId, noteId, noteData) => {
  const response = await api.put(`/api/contacts/${contactId}/notes/${noteId}?token=${token}`, noteData);
  return response.data;
};

export const deleteContactNote = async (token, contactId, noteId) => {
  await api.delete(`/api/contacts/${contactId}/notes/${noteId}?token=${token}`);
};

export const uploadNoteAudio = async (token, contactId, noteId, audioBlob) => {
  const formData = new FormData();
  formData.append('audio', audioBlob, 'recording.webm');
  const response = await api.post(
    `/api/contacts/${contactId}/notes/${noteId}/audio?token=${token}`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  );
  return response.data;
};

// Calls
export const getCallsList = async (token, { teamMemberId } = {}) => {
  const params = new URLSearchParams({ token });
  if (teamMemberId) params.append('team_member_id', teamMemberId);
  const response = await api.get(`/api/calls?${params.toString()}`);
  return response.data;
};

export const createCall = async (token, callData) => {
  const response = await api.post(`/api/calls?token=${token}`, callData);
  return response.data;
};

export const deleteCall = async (token, id) => {
  await api.delete(`/api/calls/${id}?token=${token}`);
};

export const assignCall = async (token, callId, teamMemberId) => {
  const response = await api.put(`/api/calls/${callId}/assign?token=${token}`, { team_member_id: teamMemberId });
  return response.data;
};

// Per-employee attempted/connected call counts (today / week / month) - Calls page report
export const getCallsByEmployee = async (token) => {
  const response = await api.get(`/api/analytics/calls/by-employee?token=${token}`);
  return response.data;
};

// Real send history for Email/WhatsApp/SMS (Calls page - Emails/WhatsApp tabs)
export const getCommunicationLog = async (token, channel) => {
  const params = new URLSearchParams({ token });
  if (channel) params.append('channel', channel);
  const response = await api.get(`/api/communication-log?${params.toString()}`);
  return response.data;
};

// Twilio click-to-call
export const dialCall = async (token, to, { leadId, contactId } = {}) => {
  const response = await api.post(`/api/calls/dial?token=${token}`, { to, lead_id: leadId, contact_id: contactId });
  return response.data;
};

// Claude AI note assistant
export const aiSuggestContactFollowup = async (token, contactId) => {
  const response = await api.post(`/api/contacts/${contactId}/ai-suggest?token=${token}`);
  return response.data;
};

export const aiSuggestLeadFollowup = async (token, leadId) => {
  const response = await api.post(`/api/leads/${leadId}/ai-suggest?token=${token}`);
  return response.data;
};

// Claude AI follow-up date detection (Notes modal "Detect Date" button)
export const detectFollowupDate = async (token, text) => {
  const response = await api.post(`/api/ai/detect-followup-date?token=${token}`, { text });
  return response.data;
};

// SMS via Twilio
export const sendSms = async (token, to, message, { leadId, contactId } = {}) => {
  const response = await api.post(`/api/sms/send?token=${token}`, { to, message, lead_id: leadId, contact_id: contactId });
  return response.data;
};

// WhatsApp Business API
export const sendWhatsApp = async (token, to, message, { leadId, contactId } = {}) => {
  const response = await api.post(`/api/whatsapp/send?token=${token}`, { to, message, lead_id: leadId, contact_id: contactId });
  return response.data;
};

// Email service (SMTP)
export const sendEmailReal = async (token, to, subject, body, { leadId, contactId } = {}) => {
  const response = await api.post(`/api/email/send?token=${token}`, { to, subject, body, lead_id: leadId, contact_id: contactId });
  return response.data;
};

// Mailchimp sync
export const syncMailchimp = async (token) => {
  const response = await api.post(`/api/marketing/mailchimp/sync?token=${token}`);
  return response.data;
};

// LinkedIn (OAuth - no key to pass, just kicks off the connect flow / posts once connected)
export const getLinkedInConnectUrl = async (token) => {
  const response = await api.get(`/api/integrations/linkedin/connect?token=${token}`);
  return response.data;
};

// AI Content Studio - draft marketing copy for an occasion/platform via Claude
export const generateMarketingContent = async (token, occasion, platform, notes) => {
  const response = await api.post(`/api/marketing/generate-content?token=${token}`, { occasion, platform, notes });
  return response.data;
};

// CRM chatbot (floating "Ask AI" widget) - read-only Q&A grounded in live CRM data
export const chatWithAI = async (token, message, history) => {
  const response = await api.post(`/api/ai/chat?token=${token}`, { message, history });
  return response.data;
};

export const postToLinkedIn = async (token, text) => {
  const response = await api.post(`/api/marketing/linkedin/post?token=${token}`, { text });
  return response.data;
};

// Team management
export const getTeam = async (token) => {
  const response = await api.get(`/api/team?token=${token}`);
  return response.data;
};

// The roster entry (if any) linked to the logged-in account - null if not linked yet.
export const getMyTeamMember = async (token) => {
  const response = await api.get(`/api/team/me?token=${token}`);
  return response.data;
};

// Today page - Tasks
export const getTasks = async (token, date) => {
  const response = await api.get(`/api/tasks?token=${token}&date=${date}`);
  return response.data;
};

export const getHighPriorityTasks = async (token) => {
  const response = await api.get(`/api/tasks?token=${token}&view=high_priority`);
  return response.data;
};

export const getTasksByTeamMember = async (token, teamMemberId) => {
  const response = await api.get(`/api/tasks?token=${token}&assigned_team_member_id=${teamMemberId}`);
  return response.data;
};

export const createTask = async (token, taskData) => {
  const response = await api.post(`/api/tasks?token=${token}`, taskData);
  return response.data;
};

export const updateTask = async (token, id, taskData) => {
  const response = await api.put(`/api/tasks/${id}?token=${token}`, taskData);
  return response.data;
};

export const deleteTask = async (token, id) => {
  await api.delete(`/api/tasks/${id}?token=${token}`);
};

// Today page - Meetings
export const getMeetings = async (token, date) => {
  const response = await api.get(`/api/meetings?token=${token}&date=${date}`);
  return response.data;
};

export const getMeetingsByTeamMember = async (token, teamMemberId) => {
  const response = await api.get(`/api/meetings?token=${token}&assigned_team_member_id=${teamMemberId}`);
  return response.data;
};

export const createMeeting = async (token, meetingData) => {
  const response = await api.post(`/api/meetings?token=${token}`, meetingData);
  return response.data;
};

export const updateMeeting = async (token, id, meetingData) => {
  const response = await api.put(`/api/meetings/${id}?token=${token}`, meetingData);
  return response.data;
};

export const deleteMeeting = async (token, id) => {
  await api.delete(`/api/meetings/${id}?token=${token}`);
};

export const createTeamMember = async (token, memberData) => {
  const response = await api.post(`/api/team?token=${token}`, memberData);
  return response.data;
};

export const updateTeamMember = async (token, id, memberData) => {
  const response = await api.put(`/api/team/${id}?token=${token}`, memberData);
  return response.data;
};

export const deleteTeamMember = async (token, id) => {
  await api.delete(`/api/team/${id}?token=${token}`);
};

export const getTeamAnalytics = async (token) => {
  const response = await api.get(`/api/analytics/team?token=${token}`);
  return response.data;
};

// More analytics
export const getContactsAnalytics = async (token) => {
  const response = await api.get(`/api/analytics/contacts?token=${token}`);
  return response.data;
};

export const getCallsAnalytics = async (token) => {
  const response = await api.get(`/api/analytics/calls?token=${token}`);
  return response.data;
};

// Call Dialer (Kylas "My Call Dialer" parity) - assign leads/contacts to a team member's
// dial queue, then work through it from the Calls page's Dialer tab.
export const assignToDialer = async (token, { teamMemberId, leadIds, contactIds }) => {
  const response = await api.post(`/api/dialer/assign?token=${token}`, {
    team_member_id: teamMemberId,
    lead_ids: leadIds,
    contact_ids: contactIds,
  });
  return response.data;
};

export const getDialerQueue = async (token, teamMemberId) => {
  const params = new URLSearchParams({ token });
  if (teamMemberId) params.append('team_member_id', teamMemberId);
  const response = await api.get(`/api/dialer/queue?${params.toString()}`);
  return response.data;
};

export const updateDialerStatus = async (token, id, status) => {
  const response = await api.put(`/api/dialer/queue/${id}?token=${token}`, { status });
  return response.data;
};

export const deleteDialerItem = async (token, id) => {
  await api.delete(`/api/dialer/queue/${id}?token=${token}`);
};

// Unified Activities feed (Kylas "Campaigns > Activities" parity)
export const getActivities = async (token, channel, { leadId, contactId } = {}) => {
  const params = new URLSearchParams({ token });
  if (channel) params.append('channel', channel);
  if (leadId) params.append('lead_id', leadId);
  if (contactId) params.append('contact_id', contactId);
  const response = await api.get(`/api/activities?${params.toString()}`);
  return response.data;
};

// Companies (Kylas parity - standalone directory)
export const getCompanies = async (token) => {
  const response = await api.get(`/api/companies?token=${token}`);
  return response.data;
};

export const createCompany = async (token, companyData) => {
  const response = await api.post(`/api/companies?token=${token}`, companyData);
  return response.data;
};

export const updateCompany = async (token, id, companyData) => {
  const response = await api.put(`/api/companies/${id}?token=${token}`, companyData);
  return response.data;
};

export const deleteCompany = async (token, id) => {
  await api.delete(`/api/companies/${id}?token=${token}`);
};

// Companies <-> Contacts linking
export const getCompanyContacts = async (token, companyId) => {
  const response = await api.get(`/api/companies/${companyId}/contacts?token=${token}`);
  return response.data;
};

export const linkContactCompany = async (token, contactId, companyId) => {
  const response = await api.put(`/api/contacts/${contactId}/company?token=${token}`, { company_id: companyId });
  return response.data;
};

export const getCompanyDeals = async (token, companyId) => {
  const response = await api.get(`/api/companies/${companyId}/deals?token=${token}`);
  return response.data;
};

export const getCompanyQuotations = async (token, companyId) => {
  const response = await api.get(`/api/companies/${companyId}/quotations?token=${token}`);
  return response.data;
};

export const linkDealCompany = async (token, dealId, companyId) => {
  const response = await api.put(`/api/deals/${dealId}/company?token=${token}`, { company_id: companyId });
  return response.data;
};

// Quotations (Kylas parity) - formal price quotes linked to a Lead or Contact
export const getQuotations = async (token) => {
  const response = await api.get(`/api/quotations?token=${token}`);
  return response.data;
};

export const getQuotation = async (token, id) => {
  const response = await api.get(`/api/quotations/${id}?token=${token}`);
  return response.data;
};

export const createQuotation = async (token, quotationData) => {
  const response = await api.post(`/api/quotations?token=${token}`, quotationData);
  return response.data;
};

export const updateQuotation = async (token, id, quotationData) => {
  const response = await api.put(`/api/quotations/${id}?token=${token}`, quotationData);
  return response.data;
};

export const deleteQuotation = async (token, id) => {
  await api.delete(`/api/quotations/${id}?token=${token}`);
};

export const sendQuotation = async (token, id) => {
  const response = await api.post(`/api/quotations/${id}/send?token=${token}`);
  return response.data;
};

export const getDealQuotations = async (token, dealId) => {
  const response = await api.get(`/api/deals/${dealId}/quotations?token=${token}`);
  return response.data;
};

// Tags (free-form labels on contacts/leads)
export const getTags = async (token) => {
  const response = await api.get(`/api/tags?token=${token}`);
  return response.data;
};

export const createTag = async (token, tagData) => {
  const response = await api.post(`/api/tags?token=${token}`, tagData);
  return response.data;
};

export const deleteTag = async (token, tagId) => {
  await api.delete(`/api/tags/${tagId}?token=${token}`);
};

export const getTagsForEntity = async (token, entityType, entityId) => {
  const response = await api.get(`/api/tags/for/${entityType}/${entityId}?token=${token}`);
  return response.data;
};

export const assignTag = async (token, entityType, entityId, tagId) => {
  const response = await api.post(`/api/tags/assign?token=${token}`, { entity_type: entityType, entity_id: entityId, tag_id: tagId });
  return response.data;
};

export const unassignTag = async (token, entityType, entityId, tagId) => {
  const response = await api.post(`/api/tags/unassign?token=${token}`, { entity_type: entityType, entity_id: entityId, tag_id: tagId });
  return response.data;
};

// Groups (audience segments - a contact/lead can belong to more than one)
export const getGroups = async (token) => {
  const response = await api.get(`/api/groups?token=${token}`);
  return response.data;
};

export const createGroup = async (token, groupData) => {
  const response = await api.post(`/api/groups?token=${token}`, groupData);
  return response.data;
};

export const deleteGroup = async (token, groupId) => {
  await api.delete(`/api/groups/${groupId}?token=${token}`);
};

export const getGroupsForEntity = async (token, entityType, entityId) => {
  const response = await api.get(`/api/groups/for/${entityType}/${entityId}?token=${token}`);
  return response.data;
};

export const assignGroup = async (token, entityType, entityId, groupId) => {
  const response = await api.post(`/api/groups/assign?token=${token}`, { entity_type: entityType, entity_id: entityId, group_id: groupId });
  return response.data;
};

export const unassignGroup = async (token, entityType, entityId, groupId) => {
  const response = await api.post(`/api/groups/unassign?token=${token}`, { entity_type: entityType, entity_id: entityId, group_id: groupId });
  return response.data;
};

// Custom fields (per-contact/lead key-value data, e.g. SIP Amount)
export const getCustomFields = async (token) => {
  const response = await api.get(`/api/custom-fields?token=${token}`);
  return response.data;
};

export const createCustomField = async (token, fieldData) => {
  const response = await api.post(`/api/custom-fields?token=${token}`, fieldData);
  return response.data;
};

export const deleteCustomField = async (token, fieldId) => {
  await api.delete(`/api/custom-fields/${fieldId}?token=${token}`);
};

export const getCustomFieldValuesForEntity = async (token, entityType, entityId) => {
  const response = await api.get(`/api/custom-fields/for/${entityType}/${entityId}?token=${token}`);
  return response.data;
};

export const setCustomFieldValue = async (token, payload) => {
  const response = await api.put(`/api/custom-fields/value?token=${token}`, payload);
  return response.data;
};

export default api;
