import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

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
export const getLeads = async (token, status = null) => {
  const params = new URLSearchParams();
  if (token) params.append('token', token);
  if (status) params.append('status', status);

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

// Deals
export const getDeals = async (token, stage = null) => {
  const params = new URLSearchParams();
  if (token) params.append('token', token);
  if (stage) params.append('stage', stage);

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

// Analytics
export const getDashboardAnalytics = async (token) => {
  const response = await api.get(`/api/analytics/dashboard?token=${token}`);
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

// Integrations
export const getIntegrations = async (token) => {
  const response = await api.get(`/api/integrations?token=${token}`);
  return response.data;
};

export const toggleIntegration = async (token, id, connected) => {
  const response = await api.put(`/api/integrations/${id}/toggle?token=${token}`, { connected });
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

export default api;
