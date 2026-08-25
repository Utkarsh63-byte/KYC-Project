import pytest
from app.services.risk_engine import KYCRiskEngine
from app.models.models import RiskLevel, DecisionOutcome

def test_clean_kyc_auto_approve():
    score, level, action, reasons, signals = KYCRiskEngine.evaluate_kyc_risk(
        quality_score=95.0,
        ocr_confidence=98.0,
        tamper_score=5.0,
        liveness_score=97.0,
        face_match_score=96.0,
        field_discrepancies=[]
    )
    assert score == 0.0
    assert level == RiskLevel.LOW
    assert action == DecisionOutcome.AUTO_APPROVE
    assert "low risk parameters" in reasons[-1]

def test_blurry_document_low_ocr_manual_review():
    score, level, action, reasons, signals = KYCRiskEngine.evaluate_kyc_risk(
        quality_score=50.0,  # Below 70
        ocr_confidence=75.0,  # Below 80
        tamper_score=10.0,
        liveness_score=95.0,
        face_match_score=94.0,
        field_discrepancies=[]
    )
    assert score > 20.0
    assert action == DecisionOutcome.MANUAL_REVIEW
    assert len(reasons) >= 2

def test_liveness_failure_reject():
    score, level, action, reasons, signals = KYCRiskEngine.evaluate_kyc_risk(
        quality_score=90.0,
        ocr_confidence=95.0,
        tamper_score=10.0,
        liveness_score=35.0,  # Severe liveness fail
        face_match_score=92.0,
        field_discrepancies=[]
    )
    assert action == DecisionOutcome.REJECT
    assert level in [RiskLevel.HIGH, RiskLevel.CRITICAL]

def test_name_mismatch_penalty():
    score, level, action, reasons, signals = KYCRiskEngine.evaluate_kyc_risk(
        quality_score=95.0,
        ocr_confidence=95.0,
        tamper_score=0.0,
        liveness_score=95.0,
        face_match_score=95.0,
        field_discrepancies=["Name mismatch (Profile: Rahul Sharma vs Doc: Vikram Sharma)"]
    )
    assert score >= 25.0
    assert action == DecisionOutcome.MANUAL_REVIEW
