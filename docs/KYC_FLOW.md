# KYC Onboarding Journey & Workflow Architecture

```text
LANDING / START KYC
       │
       ▼
Consent & Privacy Notice
       │
       ▼
Basic Customer Details
       │
       ▼
Document Selection & Camera Scan
       │
       ▼
OpenCV Quality Check (Blur / Glare / Res) ───▶ [Quality Low] ──▶ Re-capture Prompt
       │
       ▼
OCR Field Extraction & Normalization
       │
       ▼
FFT Tamper & Digital Artifact Check
       │
       ▼
3D Face Liveness & Face Match Check
       │
       ▼
Multi-Signal Risk Engine Evaluation
       │
 ┌─────┴──────────────────┬──────────────────┐
 ▼                        ▼                  ▼
AUTO_APPROVE        MANUAL_REVIEW         REJECT
 │                        │                  │
 ▼                        ▼                  ▼
Success Certificate   Routed to Human    Rejected
Report PDF            Review Queue       With Reasons
```
