from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.models import (
    KYCSession, Customer, Tenant, Document, ExtractedField, BiometricCheck,
    RiskAssessment, KYCSessionStatus, RiskLevel, DecisionOutcome, ReviewCase
)
from app.schemas.schemas import SandboxScenarioTrigger, KYCSessionResult
from app.services.audit_service import AuditLogger
from sqlalchemy import select

router = APIRouter(prefix="/sandbox", tags=["Bank Sandbox & Presentation Demo"])

SCENARIOS = {
    "SUCCESSFUL_PASS": {
        "customer": {"name": "Ananya Roy", "email": "ananya.roy@example.com", "phone": "+91 9876543210", "dob": "14/07/1995", "address": "Indiranagar, Bengaluru"},
        "docType": "PAN",
        "fields": [
            {"fieldName": "fullName", "value": "ANANYA ROY", "confidence": 99.2},
            {"fieldName": "fatherName", "value": "SUBHASH ROY", "confidence": 98.5},
            {"fieldName": "dob", "value": "14/07/1995", "confidence": 99.5},
            {"fieldName": "docNumber", "value": "BKNPR8765L", "confidence": 99.8}
        ],
        "qualityScore": 96.5,
        "tamperScore": 5.0,
        "livenessScore": 98.2,
        "faceMatchScore": 97.5,
        "riskScore": 8.0,
        "riskLevel": RiskLevel.LOW,
        "decision": DecisionOutcome.AUTO_APPROVE,
        "status": KYCSessionStatus.AUTO_APPROVED,
        "reasons": ["All automated verification checks passed cleanly within low risk parameters"]
    },
    "BLURRED_DOCUMENT": {
        "customer": {"name": "Karan Malhotra", "email": "karan.m@example.com", "phone": "+91 9822001122", "dob": "22/03/1990", "address": "Bandra West, Mumbai"},
        "docType": "PASSPORT",
        "fields": [
            {"fieldName": "fullName", "value": "KARAN MALHOTRA", "confidence": 74.0},
            {"fieldName": "docNumber", "value": "P8765432", "confidence": 71.5}
        ],
        "qualityScore": 48.0,
        "tamperScore": 12.0,
        "livenessScore": 95.0,
        "faceMatchScore": 94.0,
        "riskScore": 52.0,
        "riskLevel": RiskLevel.HIGH,
        "decision": DecisionOutcome.MANUAL_REVIEW,
        "status": KYCSessionStatus.MANUAL_REVIEW_REQUIRED,
        "reasons": [
            "Document image quality score (48.0/100) below threshold (70.0)",
            "OCR data extraction confidence (72.8%) below required threshold (80.0%)"
        ]
    },
    "LOW_OCR_CONFIDENCE": {
        "customer": {"name": "Deepak Kumar", "email": "deepak.k@example.com", "phone": "+91 9711223344", "dob": "05/11/1988", "address": "Connaught Place, New Delhi"},
        "docType": "AADHAAR",
        "fields": [
            {"fieldName": "fullName", "value": "Deepak Kumar", "confidence": 76.5},
            {"fieldName": "docNumber", "value": "4521 8899 1023", "confidence": 72.0}
        ],
        "qualityScore": 82.0,
        "tamperScore": 10.0,
        "livenessScore": 96.0,
        "faceMatchScore": 95.0,
        "riskScore": 42.0,
        "riskLevel": RiskLevel.MEDIUM,
        "decision": DecisionOutcome.MANUAL_REVIEW,
        "status": KYCSessionStatus.MANUAL_REVIEW_REQUIRED,
        "reasons": [
            "OCR data extraction confidence (74.2%) below required threshold (80.0%)",
            "Application exhibits borderline signals requiring human reviewer verification"
        ]
    },
    "SPOOF_ATTEMPT": {
        "customer": {"name": "Rohan Mehta", "email": "rohan.mehta@example.com", "phone": "+91 9988776655", "dob": "10/10/1993", "address": "Sector 62, Gurgaon"},
        "docType": "DRIVING_LICENSE",
        "fields": [
            {"fieldName": "fullName", "value": "ROHAN MEHTA", "confidence": 98.0},
            {"fieldName": "docNumber", "value": "DL1420110012345", "confidence": 97.5}
        ],
        "qualityScore": 92.0,
        "tamperScore": 15.0,
        "livenessScore": 32.0,
        "faceMatchScore": 96.0,
        "riskScore": 88.0,
        "riskLevel": RiskLevel.CRITICAL,
        "decision": DecisionOutcome.REJECT,
        "status": KYCSessionStatus.REJECTED,
        "reasons": [
            "Face liveness confidence (32.0%) below required threshold (85.0%)",
            "Presentation attack / screen replay spoofing indicators detected"
        ]
    },
    "FACE_MISMATCH": {
        "customer": {"name": "Siddharth Rao", "email": "sid.rao@example.com", "phone": "+91 9845012345", "dob": "02/02/1991", "address": "Jubilee Hills, Hyderabad"},
        "docType": "PAN",
        "fields": [
            {"fieldName": "fullName", "value": "SIDDHARTH RAO", "confidence": 98.0},
            {"fieldName": "docNumber", "value": "CPXPR1234Q", "confidence": 99.0}
        ],
        "qualityScore": 94.0,
        "tamperScore": 8.0,
        "livenessScore": 96.0,
        "faceMatchScore": 38.5,
        "riskScore": 82.0,
        "riskLevel": RiskLevel.CRITICAL,
        "decision": DecisionOutcome.REJECT,
        "status": KYCSessionStatus.REJECTED,
        "reasons": [
            "Face match similarity (38.5%) below verification threshold (80.0%)",
            "Uploaded document portrait photo does not match live customer selfie"
        ]
    },
    "SUSPICIOUS_SCREENSHOT": {
        "customer": {"name": "Vikram Singh", "email": "vikram.singh@example.com", "phone": "+91 9900112233", "dob": "18/09/1987", "address": "C-Scheme, Jaipur"},
        "docType": "PAN",
        "fields": [
            {"fieldName": "fullName", "value": "VIKRAM SINGH", "confidence": 95.0},
            {"fieldName": "docNumber", "value": "ABVPS9876M", "confidence": 96.0}
        ],
        "qualityScore": 88.0,
        "tamperScore": 75.0,
        "livenessScore": 96.0,
        "faceMatchScore": 95.0,
        "riskScore": 65.0,
        "riskLevel": RiskLevel.HIGH,
        "decision": DecisionOutcome.MANUAL_REVIEW,
        "status": KYCSessionStatus.MANUAL_REVIEW_REQUIRED,
        "reasons": [
            "High digital manipulation / screenshot artifact risk detected (75.0/100)",
            "Moire frequency pattern detected indicating image captured from screen"
        ]
    }
}

@router.post("/scenarios", response_model=KYCSessionResult)
async def trigger_sandbox_scenario(
    payload: SandboxScenarioTrigger,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    scen = SCENARIOS.get(payload.scenario_key)
    if not scen:
        raise HTTPException(status_code=400, detail=f"Unknown scenario key: {payload.scenario_key}")

    # 1. Resolve Tenant
    stmt_t = select(Tenant).limit(1)
    res_t = await db.execute(stmt_t)
    tenant = res_t.scalar_one_or_none()
    if not tenant:
        tenant = Tenant(name="Bank ABC International", code="BANK_ABC")
        db.add(tenant)
        await db.flush()

    # 2. Create Customer
    c_info: Dict[str, Any] = scen["customer"]  # type: ignore
    customer = Customer(
        tenant_id=tenant.id,
        full_name=str(c_info["name"]),
        email=str(c_info["email"]),
        phone=str(c_info["phone"]),
        dob=str(c_info["dob"]),
        address=str(c_info["address"])
    )
    db.add(customer)
    await db.flush()

    doc_type_val = str(scen["docType"])
    quality_val = float(scen["qualityScore"])  # type: ignore
    tamper_val = float(scen["tamperScore"])  # type: ignore
    liveness_val = float(scen["livenessScore"])  # type: ignore
    face_match_val = float(scen["faceMatchScore"])  # type: ignore
    risk_val = float(scen["riskScore"])  # type: ignore
    risk_level_val: RiskLevel = scen["riskLevel"]  # type: ignore
    decision_val: DecisionOutcome = scen["decision"]  # type: ignore
    reasons_val: List[str] = scen["reasons"]  # type: ignore
    status_val: KYCSessionStatus = scen["status"]  # type: ignore

    # 3. Create KYC Session
    session = KYCSession(
        tenant_id=tenant.id,
        customer_id=customer.id,
        status=status_val,
        risk_score=risk_val,
        risk_level=risk_level_val,
        decision=decision_val,
        decision_reasons=reasons_val
    )
    db.add(session)
    await db.flush()

    # 4. Add Document & Fields
    doc = Document(
        kyc_session_id=session.id,
        doc_type=doc_type_val,
        file_path="./data/demo_doc.jpg",
        mime_type="image/jpeg",
        file_size_bytes=245000,
        quality_score=quality_val,
        tamper_score=tamper_val
    )
    db.add(doc)
    await db.flush()

    doc_fields_output = []
    fields_list: List[Dict[str, Any]] = scen["fields"]  # type: ignore
    for f in fields_list:
        ext = ExtractedField(
            document_id=doc.id,
            field_name=str(f["fieldName"]),
            field_value=str(f["value"]),
            confidence=float(f["confidence"])
        )
        db.add(ext)
        doc_fields_output.append({"fieldName": str(f["fieldName"]), "value": str(f["value"]), "confidence": float(f["confidence"])})

    # 5. Add Biometric Check
    bio = BiometricCheck(
        kyc_session_id=session.id,
        liveness_score=liveness_val,
        liveness_status="PASSED" if liveness_val >= 85.0 else "FAILED",
        face_match_score=face_match_val,
        face_match_status="MATCH" if face_match_val >= 80.0 else "NO_MATCH",
        selfie_image_path="./data/demo_selfie.jpg"
    )
    db.add(bio)

    # 6. Add Risk Assessment
    risk_assessment = RiskAssessment(
        kyc_session_id=session.id,
        overall_risk_score=risk_val,
        risk_level=risk_level_val,
        recommended_action=decision_val,
        risk_signals={
            "qualityScore": quality_val,
            "tamperScore": tamper_val,
            "livenessScore": liveness_val,
            "faceMatchScore": face_match_val
        }
    )
    db.add(risk_assessment)

    # 7. Create Review Case if Manual Review Required
    if decision_val == DecisionOutcome.MANUAL_REVIEW:
        rc = ReviewCase(
            kyc_session_id=session.id,
            tenant_id=tenant.id,
            status="PENDING_REVIEW",
            reasons={"reasons": reasons_val}
        )
        db.add(rc)

    await AuditLogger.log_event(
        db=db,
        tenant_id=tenant.id,
        actor_id="SANDBOX_DEMO_CONTROLLER",
        actor_type="SYSTEM",
        action=f"SANDBOX_SCENARIO_TRIGGERED_{payload.scenario_key}",
        resource_type="KYCSession",
        resource_id=session.id,
        metadata={"scenario": payload.scenario_key, "decision": decision_val.value}
    )

    await db.commit()

    return KYCSessionResult(
        session_id=session.id,
        tenant_id=tenant.id,
        customer={"id": customer.id, "fullName": customer.full_name, "email": customer.email},
        status=session.status,
        risk_score=session.risk_score,
        risk_level=session.risk_level,
        decision=session.decision,
        decision_reasons=reasons_val,
        documents=[{
            "id": doc.id,
            "docType": doc.doc_type,
            "qualityScore": doc.quality_score,
            "tamperScore": doc.tamper_score,
            "fields": doc_fields_output
        }],
        biometrics={
            "livenessScore": bio.liveness_score,
            "livenessStatus": bio.liveness_status,
            "faceMatchScore": bio.face_match_score,
            "faceMatchStatus": bio.face_match_status
        },
        created_at=session.created_at,
        updated_at=session.updated_at
    )

