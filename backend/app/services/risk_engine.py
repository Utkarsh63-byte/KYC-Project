from typing import Dict, Any, List, Tuple, Optional
from app.models.models import RiskLevel, DecisionOutcome
from app.core.config import settings

class KYCRiskEngine:
    """
    Dedicated enterprise KYC Multi-Signal Risk Scoring & Policy Engine.
    Aggregates signals from Document Quality, OCR confidence, Tamper detection,
    Liveness, Face comparison, and Field consistency checks.
    """
    @staticmethod
    def evaluate_kyc_risk(
        quality_score: float,
        ocr_confidence: float,
        tamper_score: float,
        liveness_score: float,
        face_match_score: float,
        field_discrepancies: Optional[List[str]] = None
    ) -> Tuple[float, RiskLevel, DecisionOutcome, List[str], Dict[str, Any]]:

        
        field_discrepancies = field_discrepancies or []
        risk_penalty = 0.0
        reasons = []

        # 1. Document Quality Evaluation
        if quality_score < settings.QUALITY_MIN_SCORE:
            penalty = (settings.QUALITY_MIN_SCORE - quality_score) * 0.8
            risk_penalty += penalty
            reasons.append(f"Document image quality score ({quality_score}/100) below threshold ({settings.QUALITY_MIN_SCORE})")

        # 2. OCR Extraction Confidence
        if ocr_confidence < settings.OCR_MIN_CONFIDENCE:
            penalty = (settings.OCR_MIN_CONFIDENCE - ocr_confidence) * 0.9
            risk_penalty += penalty
            reasons.append(f"OCR data extraction confidence ({ocr_confidence}%) below required threshold ({settings.OCR_MIN_CONFIDENCE}%)")

        # 3. Tampering / Digital Artifacts Signal
        if tamper_score >= 50.0:
            risk_penalty += 45.0
            reasons.append(f"High digital manipulation / screenshot artifact risk detected ({tamper_score}/100)")
        elif tamper_score >= 25.0:
            risk_penalty += 20.0
            reasons.append(f"Moderate image artifact risk detected ({tamper_score}/100)")

        # 4. Biometric Face Liveness Signal
        if liveness_score < settings.LIVENESS_MIN_CONFIDENCE:
            penalty = (settings.LIVENESS_MIN_CONFIDENCE - liveness_score) * 1.5
            risk_penalty += penalty
            reasons.append(f"Face liveness confidence ({liveness_score}%) below required threshold ({settings.LIVENESS_MIN_CONFIDENCE}%)")

        # 5. Document Portrait vs Selfie Face Comparison
        if face_match_score < settings.FACE_MATCH_MIN_CONFIDENCE:
            penalty = (settings.FACE_MATCH_MIN_CONFIDENCE - face_match_score) * 1.6
            risk_penalty += penalty
            reasons.append(f"Face match similarity ({face_match_score}%) below verification threshold ({settings.FACE_MATCH_MIN_CONFIDENCE}%)")

        # 6. Customer Demographics Field Discrepancies
        if field_discrepancies:
            risk_penalty += len(field_discrepancies) * 25.0
            for disc in field_discrepancies:
                reasons.append(f"Information mismatch: {disc}")

        overall_risk_score = round(min(100.0, max(0.0, risk_penalty)), 1)

        # Map Risk Score to Risk Level
        if overall_risk_score >= 75.0:
            risk_level = RiskLevel.CRITICAL
        elif overall_risk_score >= 45.0:
            risk_level = RiskLevel.HIGH
        elif overall_risk_score >= 20.0:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        # Determine Recommended Decision Outcome
        if overall_risk_score <= settings.RISK_THRESHOLD_AUTO_APPROVE and not field_discrepancies:
            recommended_action = DecisionOutcome.AUTO_APPROVE
            reasons.append("All automated verification checks passed cleanly within low risk parameters")
        elif overall_risk_score > settings.RISK_THRESHOLD_MANUAL_REVIEW or liveness_score < 50.0 or face_match_score < 50.0:
            recommended_action = DecisionOutcome.REJECT
        else:
            recommended_action = DecisionOutcome.MANUAL_REVIEW
            reasons.append("Application exhibits borderline signals requiring human reviewer verification")

        signals = {
            "qualityScore": quality_score,
            "ocrConfidence": ocr_confidence,
            "tamperScore": tamper_score,
            "livenessScore": liveness_score,
            "faceMatchScore": face_match_score,
            "fieldDiscrepancyCount": len(field_discrepancies),
            "calculatedRiskScore": overall_risk_score
        }

        return overall_risk_score, risk_level, recommended_action, reasons, signals
