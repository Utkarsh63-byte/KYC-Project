export type KYCSessionStatus =
  | 'CREATED'
  | 'CONSENT_PENDING'
  | 'DOCUMENT_PENDING'
  | 'DOCUMENT_PROCESSED'
  | 'LIVENESS_PENDING'
  | 'BIOMETRICS_COMPLETED'
  | 'RISK_EVALUATED'
  | 'AUTO_APPROVED'
  | 'MANUAL_REVIEW_REQUIRED'
  | 'APPROVED'
  | 'REJECTED'
  | 'RETRY_REQUESTED';

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type DecisionOutcome = 'AUTO_APPROVE' | 'MANUAL_REVIEW' | 'REJECT' | 'RETRY';

export interface ExtractedField {
  fieldName: string;
  value: string;
  confidence: number;
  source?: string;
  validationStatus?: string;
}

export interface DocumentInfo {
  id: string;
  docType: string;
  qualityScore: number;
  tamperScore: number;
  fields: ExtractedField[];
}

export interface BiometricInfo {
  livenessScore: number;
  livenessStatus: string;
  faceMatchScore: number;
  faceMatchStatus: string;
}

export interface KYCSessionResult {
  session_id: string;
  tenant_id: string;
  customer: {
    id: string;
    fullName: string;
    email: string;
    phone?: string;
    dob?: string;
    address?: string;
  };
  status: KYCSessionStatus;
  risk_score: number;
  risk_level?: RiskLevel;
  decision?: DecisionOutcome;
  decision_reasons: string[];
  documents: DocumentInfo[];
  biometrics?: BiometricInfo;
  created_at: string;
  updated_at: string;
}

export interface ReviewCaseItem {
  caseId: string;
  sessionId: string;
  customer: {
    fullName: string;
    email: string;
    phone?: string;
    dob?: string;
    address?: string;
  };
  document: {
    docType: string;
    qualityScore: number;
    tamperScore: number;
    extractedFields: ExtractedField[];
  };
  biometrics: {
    livenessScore: number;
    faceMatchScore: number;
  };
  risk: {
    score: number;
    level: RiskLevel;
    reasons: string[];
  };
  createdAt: string;
}

export interface AnalyticsSummary {
  total_applications: number;
  approved_count: number;
  rejected_count: number;
  manual_review_count: number;
  avg_verification_time_seconds: number;
  auto_pass_rate_percentage: number;
  manual_review_rate_percentage: number;
  failure_reasons_breakdown: Record<string, number>;
  risk_distribution: Record<string, number>;
}

export interface AuditLogItem {
  id: string;
  tenant_id: string;
  actor_id: string;
  actor_type: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  ip_address?: string;
  user_agent?: string;
  correlation_id?: string;
  result: string;
  created_at: string;
}

