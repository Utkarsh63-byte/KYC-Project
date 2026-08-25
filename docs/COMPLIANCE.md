# Regulatory Compliance & Privacy Architecture

## 1. RBI KYC Master Direction Alignment
- **Remote Onboarding**: Incorporates live camera capture, active face liveness, document quality controls, and identity verification.
- **Audit Trails**: Records complete timestamped audit logs for every session, document upload, verification score, and human officer review action.

## 2. Privacy & Data Protection (DPDP Act)
- **Explicit Consent**: Captures purpose-limited consent prior to processing biometric or document data.
- **Data Minimization & Retention**: Configurable data retention policies allowing scheduled deletion of temporary media files.
- **PII Masking**: Hides full PAN / Aadhaar numbers in ordinary reviewer log views.

## 3. Human Oversight & Explainable Decisions
- Automated AI decisions are non-final for borderline cases; routed to trained human officers via the Reviewer Portal.
- Machine-readable reason codes are stored for regulatory audit reporting.
