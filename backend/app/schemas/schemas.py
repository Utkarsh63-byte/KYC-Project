from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from app.models.models import KYCSessionStatus, RiskLevel, DecisionOutcome, UserRole

# Auth & User Schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole
    tenant_id: str
    user_id: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole = UserRole.KYC_OFFICER
    tenant_id: str

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: UserRole
    tenant_id: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# KYC Session Schemas
class KYCSessionCreate(BaseModel):
    external_customer_id: Optional[str] = None
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    dob: Optional[str] = None
    address: Optional[str] = None

class ConsentSubmit(BaseModel):
    purpose: str = "Digital Identity Verification for Bank Account Onboarding"
    policy_version: str = "v2.1"
    consent_granted: bool = True

class ExtractedFieldSchema(BaseModel):
    fieldName: str
    value: str
    confidence: float
    source: str = "ocr"
    validationStatus: str = "VALID"

class DocumentUploadResponse(BaseModel):
    document_id: str
    kyc_session_id: str
    doc_type: str
    quality_score: float
    quality_checks: Dict[str, Any]
    tamper_score: float
    tamper_checks: Dict[str, Any]
    extracted_fields: List[ExtractedFieldSchema]

class LivenessVerificationRequest(BaseModel):
    selfie_base64: str
    challenge_data: Optional[Dict[str, Any]] = None

class BiometricResponse(BaseModel):
    biometric_id: str
    liveness_score: float
    liveness_status: str
    face_match_score: float
    face_match_status: str

class RiskEvaluationResult(BaseModel):
    session_id: str
    overall_risk_score: float
    risk_level: RiskLevel
    recommended_action: DecisionOutcome
    reasons: List[str]
    signals: Dict[str, Any]

class KYCSessionResult(BaseModel):
    session_id: str
    tenant_id: str
    customer: Dict[str, Any]
    status: KYCSessionStatus
    risk_score: float
    risk_level: Optional[RiskLevel]
    decision: Optional[DecisionOutcome]
    decision_reasons: List[str]
    documents: List[Dict[str, Any]]
    biometrics: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

# Reviewer & Admin Portal Schemas
class ReviewActionSubmit(BaseModel):
    decision: str  # APPROVED, REJECTED, RETRY_REQUESTED
    reviewer_notes: Optional[str] = None
    reasons: Optional[List[str]] = None

class AuditLogResponse(BaseModel):
    id: str
    actor_id: str
    actor_type: str
    action: str
    resource_type: str
    resource_id: str
    ip_address: Optional[str]
    correlation_id: Optional[str]
    result: str
    metadata_json: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True

class AnalyticsSummaryResponse(BaseModel):
    total_applications: int
    approved_count: int
    rejected_count: int
    manual_review_count: int
    avg_verification_time_seconds: float
    auto_pass_rate_percentage: float
    manual_review_rate_percentage: float
    failure_reasons_breakdown: Dict[str, int]
    risk_distribution: Dict[str, int]

# Sandbox Demo Schema
class SandboxScenarioTrigger(BaseModel):
    scenario_key: str  # SUCCESSFUL_PASS, BLURRED_DOCUMENT, LOW_OCR, SPOOF_ATTEMPT, FACE_MISMATCH, SUSPICIOUS_SCREENSHOT, HIGH_RISK
