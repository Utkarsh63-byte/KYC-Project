import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, DateTime, Float, Integer, Boolean, Text, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    TENANT_ADMIN = "TENANT_ADMIN"
    KYC_OFFICER = "KYC_OFFICER"
    REVIEWER = "REVIEWER"
    COMPLIANCE_OFFICER = "COMPLIANCE_OFFICER"
    AUDITOR = "AUDITOR"
    API_CLIENT = "API_CLIENT"
    CUSTOMER = "CUSTOMER"

class KYCSessionStatus(str, enum.Enum):
    CREATED = "CREATED"
    CONSENT_PENDING = "CONSENT_PENDING"
    DOCUMENT_PENDING = "DOCUMENT_PENDING"
    DOCUMENT_PROCESSED = "DOCUMENT_PROCESSED"
    LIVENESS_PENDING = "LIVENESS_PENDING"
    BIOMETRICS_COMPLETED = "BIOMETRICS_COMPLETED"
    RISK_EVALUATED = "RISK_EVALUATED"
    AUTO_APPROVED = "AUTO_APPROVED"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RETRY_REQUESTED = "RETRY_REQUESTED"

class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class DecisionOutcome(str, enum.Enum):
    AUTO_APPROVE = "AUTO_APPROVE"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    REJECT = "REJECT"
    RETRY = "RETRY"

class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    webhook_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    webhook_secret: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    users: Mapped[List["User"]] = relationship("User", back_populates="tenant")
    kyc_sessions: Mapped[List["KYCSession"]] = relationship("KYCSession", back_populates="tenant")

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), default=UserRole.KYC_OFFICER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")

class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    external_customer_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(150), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    dob: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    kyc_sessions: Mapped[List["KYCSession"]] = relationship("KYCSession", back_populates="customer")

class KYCSession(Base):
    __tablename__ = "kyc_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), nullable=False)
    status: Mapped[KYCSessionStatus] = mapped_column(SQLEnum(KYCSessionStatus), default=KYCSessionStatus.CREATED)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    risk_level: Mapped[Optional[RiskLevel]] = mapped_column(SQLEnum(RiskLevel), nullable=True)
    decision: Mapped[Optional[DecisionOutcome]] = mapped_column(SQLEnum(DecisionOutcome), nullable=True)
    decision_reasons: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="kyc_sessions")
    customer: Mapped["Customer"] = relationship("Customer", back_populates="kyc_sessions")
    documents: Mapped[List["Document"]] = relationship("Document", back_populates="kyc_session", cascade="all, delete-orphan")
    biometrics: Mapped[List["BiometricCheck"]] = relationship("BiometricCheck", back_populates="kyc_session", cascade="all, delete-orphan")
    risk_assessments: Mapped[List["RiskAssessment"]] = relationship("RiskAssessment", back_populates="kyc_session", cascade="all, delete-orphan")
    review_cases: Mapped[List["ReviewCase"]] = relationship("ReviewCase", back_populates="kyc_session", cascade="all, delete-orphan")

class ConsentRecord(Base):
    __tablename__ = "consent_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    kyc_session_id: Mapped[str] = mapped_column(String(36), ForeignKey("kyc_sessions.id"), nullable=False)
    purpose: Mapped[str] = mapped_column(String(255), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(20), nullable=False)
    consent_granted: Mapped[bool] = mapped_column(Boolean, default=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    kyc_session_id: Mapped[str] = mapped_column(String(36), ForeignKey("kyc_sessions.id"), nullable=False)
    doc_type: Mapped[str] = mapped_column(String(50), nullable=False)  # PAN, AADHAAR, PASSPORT, DRIVING_LICENSE, VOTER_ID
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    quality_checks: Mapped[dict] = mapped_column(JSON, default=dict)
    tamper_score: Mapped[float] = mapped_column(Float, default=0.0)
    tamper_checks: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    kyc_session: Mapped["KYCSession"] = relationship("KYCSession", back_populates="documents")
    fields: Mapped[List["ExtractedField"]] = relationship("ExtractedField", back_populates="document", cascade="all, delete-orphan")

class ExtractedField(Base):
    __tablename__ = "extracted_fields"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id"), nullable=False)
    field_name: Mapped[str] = mapped_column(String(50), nullable=False)  # fullName, dob, docNumber, address, issueDate, expiryDate
    field_value: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    source: Mapped[str] = mapped_column(String(50), default="ocr")
    validation_status: Mapped[str] = mapped_column(String(20), default="VALID")  # VALID, INVALID, SUSPECTED
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    document: Mapped["Document"] = relationship("Document", back_populates="fields")

class BiometricCheck(Base):
    __tablename__ = "biometric_checks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    kyc_session_id: Mapped[str] = mapped_column(String(36), ForeignKey("kyc_sessions.id"), nullable=False)
    liveness_score: Mapped[float] = mapped_column(Float, default=0.0)
    liveness_status: Mapped[str] = mapped_column(String(20), default="PASSED")
    face_match_score: Mapped[float] = mapped_column(Float, default=0.0)
    face_match_status: Mapped[str] = mapped_column(String(20), default="MATCH")
    selfie_image_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    raw_response: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    kyc_session: Mapped["KYCSession"] = relationship("KYCSession", back_populates="biometrics")

class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    kyc_session_id: Mapped[str] = mapped_column(String(36), ForeignKey("kyc_sessions.id"), nullable=False)
    overall_risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    risk_level: Mapped[RiskLevel] = mapped_column(SQLEnum(RiskLevel), default=RiskLevel.LOW)
    recommended_action: Mapped[DecisionOutcome] = mapped_column(SQLEnum(DecisionOutcome), default=DecisionOutcome.AUTO_APPROVE)
    risk_signals: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    kyc_session: Mapped["KYCSession"] = relationship("KYCSession", back_populates="risk_assessments")

class ReviewCase(Base):
    __tablename__ = "review_cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    kyc_session_id: Mapped[str] = mapped_column(String(36), ForeignKey("kyc_sessions.id"), nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    reviewer_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="PENDING_REVIEW") # PENDING_REVIEW, IN_REVIEW, APPROVED, REJECTED, RETRY_REQUESTED
    reasons: Mapped[dict] = mapped_column(JSON, default=dict)
    reviewer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decision: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    kyc_session: Mapped["KYCSession"] = relationship("KYCSession", back_populates="review_cases")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    actor_id: Mapped[str] = mapped_column(String(100), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(50), default="SYSTEM") # CUSTOMER, OFFICER, SYSTEM, API
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(100), nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    correlation_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    result: Mapped[str] = mapped_column(String(20), default="SUCCESS")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    target_url: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    delivery_status: Mapped[str] = mapped_column(String(20), default="SUCCESS") # SUCCESS, FAILED, RETRYING
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
