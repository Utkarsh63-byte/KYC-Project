import axios from 'axios';
import { KYCSessionResult, ReviewCaseItem, AnalyticsSummary } from '../types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
const API_BASE = `${BASE_URL}/api/v1`;

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
    'X-Tenant-ID': 'BANK_ABC'
  }
});


export const kycApi = {
  createSession: async (data: { fullName: string; email: string; phone?: string; dob?: string; address?: string }) => {
    const res = await api.post<KYCSessionResult>('/kyc/sessions', {
      full_name: data.fullName,
      email: data.email,
      phone: data.phone,
      dob: data.dob,
      address: data.address
    });
    return res.data;
  },

  submitConsent: async (sessionId: string) => {
    const res = await api.post(`/kyc/sessions/${sessionId}/consent`, {
      purpose: 'Digital Identity Verification for Bank Account Onboarding',
      policy_version: 'v2.1',
      consent_granted: true
    });
    return res.data;
  },

  uploadDocument: async (sessionId: string, docType: string, file: File) => {
    const formData = new FormData();
    formData.append('doc_type', docType);
    formData.append('file', file);

    const res = await api.post(`/kyc/sessions/${sessionId}/documents`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return res.data;
  },

  verifyLiveness: async (sessionId: string, selfieBase64: string) => {
    const res = await api.post(`/kyc/sessions/${sessionId}/liveness`, {
      selfie_base64: selfieBase64
    });
    return res.data;
  },

  executeVerification: async (sessionId: string) => {
    const res = await api.post(`/kyc/sessions/${sessionId}/verify`);
    return res.data;
  },

  getSessionResult: async (sessionId: string) => {
    const res = await api.get<KYCSessionResult>(`/kyc/sessions/${sessionId}/result`);
    return res.data;
  },

  getReportPdfUrl: (sessionId: string) => {
    return `${API_BASE}/kyc/sessions/${sessionId}/report/pdf`;
  }
};

export const adminApi = {
  getApplications: async () => {
    const res = await api.get('/admin/kyc/applications');
    return res.data;
  },

  getReviewCases: async () => {
    const res = await api.get<ReviewCaseItem[]>('/admin/reviews');
    return res.data;
  },

  submitReviewDecision: async (caseId: string, decision: 'APPROVED' | 'REJECTED' | 'RETRY_REQUESTED', notes: string) => {
    const res = await api.post(`/admin/reviews/${caseId}/action`, {
      decision,
      reviewer_notes: notes
    });
    return res.data;
  },

  getAnalytics: async () => {
    const res = await api.get<AnalyticsSummary>('/admin/analytics');
    return res.data;
  },

  getAuditLogs: async () => {
    const res = await api.get('/admin/audit-logs');
    return res.data;
  }
};

export const sandboxApi = {
  triggerScenario: async (scenarioKey: string) => {
    const res = await api.post<KYCSessionResult>('/sandbox/scenarios', {
      scenario_key: scenarioKey
    });
    return res.data;
  }
};
