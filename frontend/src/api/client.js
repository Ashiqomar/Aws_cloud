import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

// AWS API calls
export const connectAWSAccount = (data) => apiClient.post('/aws/connect', data);
export const triggerAWSSync = (tenantId) => apiClient.post('/aws/sync', { tenant_id: tenantId });
export const getTenants = () => apiClient.get('/tenants');
export const seedDemoData = () => apiClient.post('/demo/seed');

// Cost analytics
export const getCostSummary = (params) => apiClient.get('/costs/summary', { params });

// Recommendations
export const getRecommendations = (params) => apiClient.get('/recommendations', { params });
export const getRecommendationsSummary = (params) => apiClient.get('/recommendations/summary', { params });
export const triggerAnalysis = (tenantId) => apiClient.post(`/recommendations/analyze?tenant_id=${tenantId}`);

// AI Advisor Insights
export const getAISummary = (params) => apiClient.get('/ai/summary', { params });

// Remediation Actions
export const applyRemediation = (data) => apiClient.post('/remediate/apply', data);
