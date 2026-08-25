import base64
import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.models import (
    KYCSession, Customer, Tenant, Document, ExtractedField, BiometricCheck,
    RiskAssessment, ConsentRecord, KYCSessionStatus, RiskLevel, DecisionOutcome, ReviewCase,
    generate_uuid
)

from app.schemas.schemas import (
    KYCSessionCreate, ConsentSubmit, DocumentUploadResponse, ExtractedFieldSchema,
    LivenessVerificationRequest, BiometricResponse, RiskEvaluationResult, KYCSessionResult
)
from app.providers.ocr_provider import get_ocr_provider
from app.providers.biometrics_provider import get_liveness_provider, get_face_match_provider
from app.providers.storage_provider import get_storage_provider
from app.processing.document_quality import DocumentQualityAnalyzer
from app.processing.tamper_detector import DocumentTamperDetector
from app.services.risk_engine import KYCRiskEngine
from app.services.audit_service import AuditLogger
from app.services.pdf_generator import KYCReportPDFGenerator

router = APIRouter(prefix="/kyc/sessions", tags=["Customer KYC Journey"])

@router.post("", response_model=KYCSessionResult)
async def create_kyc_session(
    payload: KYCSessionCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    tenant_id = getattr(request.state, "tenant_id", "default_bank_tenant")
    
    # 1. Resolve or Create Tenant
    stmt_tenant = select(Tenant).where(Tenant.id == tenant_id)
    res_tenant = await db.execute(stmt_tenant)
    tenant = res_tenant.scalar_one_or_none()
    if not tenant:
        stmt_tenant_code = select(Tenant).limit(1)
        res = await db.execute(stmt_tenant_code)
        tenant = res.scalar_one_or_none()
        if not tenant:
            tenant = Tenant(name="Bank ABC International", code="BANK_ABC")
            db.add(tenant)
            await db.flush()
        tenant_id = tenant.id

    # 2. Create Customer Profile
    customer = Customer(
        tenant_id=tenant_id,
        external_customer_id=payload.external_customer_id,
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        dob=payload.dob,
        address=payload.address
    )
    db.add(customer)
    await db.flush()

    # 3. Initialize KYC Session
    kyc_session = KYCSession(
        tenant_id=tenant_id,
        customer_id=customer.id,
        status=KYCSessionStatus.CREATED,
        ip_address=request.client.host if request.client else "127.0.0.1",
        user_agent=request.headers.get("User-Agent", "Unknown")
    )
    db.add(kyc_session)
    await db.flush()

    # 4. Audit Log
    await AuditLogger.log_event(
        db=db,
        tenant_id=tenant_id,
        actor_id=customer.id,
        actor_type="CUSTOMER",
        action="KYC_SESSION_CREATED",
        resource_type="KYCSession",
        resource_id=kyc_session.id,
        ip_address=kyc_session.ip_address,
        user_agent=kyc_session.user_agent,
        correlation_id=getattr(request.state, "correlation_id", None)
    )

    await db.commit()

    return KYCSessionResult(
        session_id=kyc_session.id,
        tenant_id=tenant_id,
        customer={"id": customer.id, "fullName": customer.full_name, "email": customer.email},
        status=kyc_session.status,
        risk_score=0.0,
        risk_level=None,
        decision=None,
        decision_reasons=[],
        documents=[],
        biometrics=None,
        created_at=kyc_session.created_at,
        updated_at=kyc_session.updated_at
    )

@router.post("/{session_id}/consent")
async def submit_consent(
    session_id: str,
    payload: ConsentSubmit,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(KYCSession).where(KYCSession.id == session_id)
    res = await db.execute(stmt)
    kyc_session = res.scalar_one_or_none()
    if not kyc_session:
        raise HTTPException(status_code=404, detail="KYC Session not found")

    consent = ConsentRecord(
        id=generate_uuid(),
        kyc_session_id=session_id,
        purpose=payload.purpose,
        policy_version=payload.policy_version,
        consent_granted=payload.consent_granted,
        ip_address=request.client.host if request.client else "127.0.0.1",
        user_agent=request.headers.get("User-Agent")
    )
    db.add(consent)
    await db.flush()

    kyc_session.status = KYCSessionStatus.DOCUMENT_PENDING
    
    await AuditLogger.log_event(
        db=db,
        tenant_id=kyc_session.tenant_id,
        actor_id=kyc_session.customer_id,
        actor_type="CUSTOMER",
        action="PRIVACY_CONSENT_GRANTED",
        resource_type="ConsentRecord",
        resource_id=consent.id,
        correlation_id=getattr(request.state, "correlation_id", None)
    )

    
    await db.commit()
    return {"message": "Consent recorded successfully", "status": kyc_session.status}

@router.post("/{session_id}/documents", response_model=DocumentUploadResponse)
async def upload_document(
    session_id: str,
    doc_type: str = Form(...),  # PAN, AADHAAR, PASSPORT, DRIVING_LICENSE, VOTER_ID
    file: UploadFile = File(...),
    request: Request = None,  # type: ignore[assignment]
    db: AsyncSession = Depends(get_db)
):


    stmt = select(KYCSession).where(KYCSession.id == session_id)
    res = await db.execute(stmt)
    kyc_session = res.scalar_one_or_none()
    if not kyc_session:
        raise HTTPException(status_code=404, detail="KYC Session not found")

    file_bytes = await file.read()
    
    # 1. Save File to Storage Provider
    storage_provider = get_storage_provider()
    file_path = await storage_provider.save_file(
        tenant_id=kyc_session.tenant_id,
        session_id=session_id,
        file_bytes=file_bytes,
        file_name=file.filename or "document.jpg",
        mime_type=file.content_type or "image/jpeg"
    )

    # 2. Document Quality Check (Blur, Glare, Resolution)
    quality_score, quality_checks = DocumentQualityAnalyzer.analyze_image_quality(file_bytes)

    # 3. Document Tamper & Digital Artifact Detection
    tamper_score, tamper_checks = DocumentTamperDetector.inspect_document_risk(file_bytes, file.filename or "")

    # 4. OCR Extraction via Provider
    ocr_provider = get_ocr_provider()
    extracted_fields_raw, avg_conf = await ocr_provider.extract_text_and_fields(file_bytes, doc_type)

    # 5. Persist Document & Fields
    doc_model = Document(
        kyc_session_id=session_id,
        doc_type=doc_type.upper(),
        file_path=file_path,
        mime_type=file.content_type or "image/jpeg",
        file_size_bytes=len(file_bytes),
        quality_score=quality_score,
        quality_checks=quality_checks,
        tamper_score=tamper_score,
        tamper_checks=tamper_checks
    )
    db.add(doc_model)
    await db.flush()

    extracted_schemas = []
    for field in extracted_fields_raw:
        ext_field = ExtractedField(
            document_id=doc_model.id,
            field_name=field["fieldName"],
            field_value=field["value"],
            confidence=field["confidence"],
            source=field["source"],
            validation_status=field["validationStatus"]
        )
        db.add(ext_field)
        extracted_schemas.append(ExtractedFieldSchema(
            fieldName=field["fieldName"],
            value=field["value"],
            confidence=field["confidence"],
            source=field["source"],
            validationStatus=field["validationStatus"]
        ))

    kyc_session.status = KYCSessionStatus.LIVENESS_PENDING
    
    await AuditLogger.log_event(
        db=db,
        tenant_id=kyc_session.tenant_id,
        actor_id=kyc_session.customer_id,
        actor_type="CUSTOMER",
        action="DOCUMENT_UPLOADED_AND_PROCESSED",
        resource_type="Document",
        resource_id=doc_model.id,
        metadata={"doc_type": doc_type, "quality_score": quality_score, "tamper_score": tamper_score}
    )

    await db.commit()

    return DocumentUploadResponse(
        document_id=doc_model.id,
        kyc_session_id=session_id,
        doc_type=doc_model.doc_type,
        quality_score=quality_score,
        quality_checks=quality_checks,
        tamper_score=tamper_score,
        tamper_checks=tamper_checks,
        extracted_fields=extracted_schemas
    )

@router.post("/{session_id}/liveness", response_model=BiometricResponse)
async def process_liveness_and_face_match(
    session_id: str,
    payload: LivenessVerificationRequest,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(KYCSession).options(selectinload(KYCSession.documents)).where(KYCSession.id == session_id)
    res = await db.execute(stmt)
    kyc_session = res.scalar_one_or_none()
    if not kyc_session:
        raise HTTPException(status_code=404, detail="KYC Session not found")

    try:
        header, encoded = payload.selfie_base64.split(",", 1) if "," in payload.selfie_base64 else ("", payload.selfie_base64)
        selfie_bytes = base64.b64decode(encoded)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 selfie image stream")

    # 1. Run Liveness Verification
    liveness_provider = get_liveness_provider()
    liveness_score, liveness_status, liveness_meta = await liveness_provider.verify_liveness(
        selfie_bytes=selfie_bytes,
        challenge_data=payload.challenge_data
    )

    # 2. Run Face Matching against Document Portrait
    doc_photo_bytes = selfie_bytes  # Default fallback
    if kyc_session.documents:
        doc = kyc_session.documents[0]
        if os.path.exists(doc.file_path):
            with open(doc.file_path, "rb") as f:
                doc_photo_bytes = f.read()

    face_match_provider = get_face_match_provider()
    face_score, face_status, face_meta = await face_match_provider.compare_faces(
        document_photo_bytes=doc_photo_bytes,
        selfie_bytes=selfie_bytes
    )

    # 3. Save Selfie to Storage Provider
    storage_provider = get_storage_provider()
    selfie_path = await storage_provider.save_file(
        tenant_id=kyc_session.tenant_id,
        session_id=session_id,
        file_bytes=selfie_bytes,
        file_name="selfie_liveness.jpg",
        mime_type="image/jpeg"
    )

    # 4. Save Biometric Record
    biometric_model = BiometricCheck(
        kyc_session_id=session_id,
        liveness_score=liveness_score,
        liveness_status=liveness_status,
        face_match_score=face_score,
        face_match_status=face_status,
        selfie_image_path=selfie_path,
        raw_response={"liveness": liveness_meta, "faceMatch": face_meta}
    )
    db.add(biometric_model)

    kyc_session.status = KYCSessionStatus.BIOMETRICS_COMPLETED
    
    await AuditLogger.log_event(
        db=db,
        tenant_id=kyc_session.tenant_id,
        actor_id=kyc_session.customer_id,
        actor_type="CUSTOMER",
        action="BIOMETRIC_LIVENESS_AND_FACE_MATCH_COMPLETED",
        resource_type="BiometricCheck",
        resource_id=biometric_model.id,
        metadata={"liveness_score": liveness_score, "face_score": face_score}
    )

    await db.commit()

    return BiometricResponse(
        biometric_id=biometric_model.id,
        liveness_score=liveness_score,
        liveness_status=liveness_status,
        face_match_score=face_score,
        face_match_status=face_status
    )

@router.post("/{session_id}/verify", response_model=RiskEvaluationResult)
async def execute_verification(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(KYCSession)
        .options(
            selectinload(KYCSession.customer),
            selectinload(KYCSession.documents).selectinload(Document.fields),
            selectinload(KYCSession.biometrics)
        )
        .where(KYCSession.id == session_id)
    )
    res = await db.execute(stmt)
    kyc_session = res.scalar_one_or_none()
    if not kyc_session:
        raise HTTPException(status_code=404, detail="KYC Session not found")

    quality_score = 90.0
    tamper_score = 0.0
    ocr_confidence = 95.0
    if kyc_session.documents:
        doc = kyc_session.documents[0]
        quality_score = doc.quality_score
        tamper_score = doc.tamper_score
        if doc.fields:
            ocr_confidence = sum(f.confidence for f in doc.fields) / max(len(doc.fields), 1)

    liveness_score = 95.0
    face_match_score = 95.0
    if kyc_session.biometrics:
        bio = kyc_session.biometrics[0]
        liveness_score = bio.liveness_score
        face_match_score = bio.face_match_score

    # Check field consistency between customer profile & document extracted fields
    discrepancies = []
    if kyc_session.customer and kyc_session.documents and kyc_session.documents[0].fields:
        doc_fields = {f.field_name: f.field_value for f in kyc_session.documents[0].fields}
        customer_name = kyc_session.customer.full_name.upper().strip()
        doc_name = doc_fields.get("fullName", "").upper().strip()
        if doc_name and doc_name != "NOT_DETECTED" and customer_name:
            cust_tokens = set(customer_name.split())
            doc_tokens = set(doc_name.split())
            common_tokens = cust_tokens.intersection(doc_tokens)
            if not common_tokens and customer_name not in doc_name and doc_name not in customer_name:
                discrepancies.append(f"Name mismatch (Profile: {kyc_session.customer.full_name} vs Doc: {doc_fields.get('fullName')})")

        # DOB Cross-Check
        cust_dob = getattr(kyc_session.customer, "dob", None)
        doc_dob = doc_fields.get("dob")
        if cust_dob and doc_dob and doc_dob != "NOT_DETECTED":
            clean_cust = cust_dob.replace('-', '/').replace('.', '/').strip()
            clean_doc = doc_dob.replace('-', '/').replace('.', '/').strip()
            if clean_cust != clean_doc:
                discrepancies.append(f"DOB discrepancy (Profile: {cust_dob} vs Doc: {doc_dob})")


    # Evaluate Risk Engine
    risk_score, risk_level, recommended_action, reasons, signals = KYCRiskEngine.evaluate_kyc_risk(
        quality_score=quality_score,
        ocr_confidence=ocr_confidence,
        tamper_score=tamper_score,
        liveness_score=liveness_score,
        face_match_score=face_match_score,
        field_discrepancies=discrepancies
    )

    # Persist Risk Assessment
    risk_model = RiskAssessment(
        kyc_session_id=session_id,
        overall_risk_score=risk_score,
        risk_level=risk_level,
        recommended_action=recommended_action,
        risk_signals=signals
    )
    db.add(risk_model)

    # Update KYC Session Decision State
    kyc_session.risk_score = risk_score
    kyc_session.risk_level = risk_level
    kyc_session.decision = recommended_action
    kyc_session.decision_reasons = reasons  # type: ignore[assignment]


    if recommended_action == DecisionOutcome.AUTO_APPROVE:
        kyc_session.status = KYCSessionStatus.AUTO_APPROVED
    elif recommended_action == DecisionOutcome.MANUAL_REVIEW:
        kyc_session.status = KYCSessionStatus.MANUAL_REVIEW_REQUIRED
        # Create Human Review Case
        review_case = ReviewCase(
            kyc_session_id=session_id,
            tenant_id=kyc_session.tenant_id,
            status="PENDING_REVIEW",
            reasons={"reasons": reasons, "signals": signals}
        )
        db.add(review_case)
    else:
        kyc_session.status = KYCSessionStatus.REJECTED

    await AuditLogger.log_event(
        db=db,
        tenant_id=kyc_session.tenant_id,
        actor_id="SYSTEM_RISK_ENGINE",
        actor_type="SYSTEM",
        action="KYC_VERIFICATION_EVALUATED",
        resource_type="KYCSession",
        resource_id=session_id,
        metadata={"risk_score": risk_score, "decision": recommended_action.value}
    )

    await db.commit()

    return RiskEvaluationResult(
        session_id=session_id,
        overall_risk_score=risk_score,
        risk_level=risk_level,
        recommended_action=recommended_action,
        reasons=reasons,
        signals=signals
    )

@router.get("/{session_id}/result", response_model=KYCSessionResult)
async def get_kyc_session_result(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(KYCSession)
        .options(
            selectinload(KYCSession.customer),
            selectinload(KYCSession.documents).selectinload(Document.fields),
            selectinload(KYCSession.biometrics)
        )
        .where(KYCSession.id == session_id)
    )
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="KYC Session not found")

    docs = []
    for d in session.documents:
        docs.append({
            "id": d.id,
            "docType": d.doc_type,
            "qualityScore": d.quality_score,
            "tamperScore": d.tamper_score,
            "fields": [{"fieldName": f.field_name, "value": f.field_value, "confidence": f.confidence} for f in d.fields]
        })

    bio_dict = None
    if session.biometrics:
        b = session.biometrics[0]
        bio_dict = {
            "livenessScore": b.liveness_score,
            "livenessStatus": b.liveness_status,
            "faceMatchScore": b.face_match_score,
            "faceMatchStatus": b.face_match_status
        }

    reasons_list: List[str] = list(session.decision_reasons) if session.decision_reasons and isinstance(session.decision_reasons, list) else []

    return KYCSessionResult(
        session_id=session.id,
        tenant_id=session.tenant_id,
        customer={"id": session.customer.id, "fullName": session.customer.full_name, "email": session.customer.email},
        status=session.status,
        risk_score=session.risk_score,
        risk_level=session.risk_level,
        decision=session.decision,
        decision_reasons=reasons_list,
        documents=docs,
        biometrics=bio_dict,
        created_at=session.created_at,
        updated_at=session.updated_at
    )


@router.get("/{session_id}/report/pdf")
async def download_kyc_pdf_report(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(KYCSession)
        .options(
            selectinload(KYCSession.tenant),
            selectinload(KYCSession.customer),
            selectinload(KYCSession.documents).selectinload(Document.fields),
            selectinload(KYCSession.biometrics)
        )
        .where(KYCSession.id == session_id)
    )
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="KYC Session not found")

    tenant_name = session.tenant.name if session.tenant else "Bank ABC International"
    customer_name = session.customer.full_name if session.customer else "Customer"
    customer_email = session.customer.email if session.customer else "customer@example.com"
    doc_type = session.documents[0].doc_type if session.documents else "PAN"
    
    quality_score = session.documents[0].quality_score if session.documents else 95.0
    extracted_fields = [{"fieldName": f.field_name, "value": f.field_value, "confidence": f.confidence, "validationStatus": f.validation_status} for f in session.documents[0].fields] if session.documents and session.documents[0].fields else []

    liveness_score = session.biometrics[0].liveness_score if session.biometrics else 98.0
    face_match_score = session.biometrics[0].face_match_score if session.biometrics else 96.0

    reasons_list: List[str] = list(session.decision_reasons) if session.decision_reasons and isinstance(session.decision_reasons, list) else ["All automated checks passed"]

    pdf_bytes = KYCReportPDFGenerator.generate_report_pdf(
        session_id=session.id,
        tenant_name=tenant_name,
        customer_name=customer_name,
        customer_email=customer_email,
        doc_type=doc_type,
        status=session.status.value,
        risk_score=session.risk_score,
        risk_level=session.risk_level.value if session.risk_level else "LOW",
        decision=session.decision.value if session.decision else "AUTO_APPROVE",
        decision_reasons=reasons_list,
        extracted_fields=extracted_fields,
        quality_score=quality_score,
        liveness_score=liveness_score,
        face_match_score=face_match_score
    )


    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=KYC_Certificate_{session_id[:8]}.pdf"}
    )
