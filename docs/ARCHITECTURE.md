# Architecture Documentation

## System Architecture

```text
                             ┌───────────────────────────────┐
                             │       Customer Web App        │
                             └───────────────┬───────────────┘
                                             │ REST API / HTTPS
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                   API Gateway / FastAPI                                 │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│ Security Headers │ Tenant Scope Middleware │ Rate Limiter │ Correlation ID │ Auth Guard │
└──────────────────────────────┬───────────────────────────────┬──────────────────────────┘
                               │                               │
                               ▼                               ▼
             ┌──────────────────────────────────┐    ┌──────────────────────────────────┐
             │     KYC Session Orchestrator     │    │      Reviewer & Admin Portal     │
             └─────────────────┬────────────────┘    └─────────────────┬────────────────┘
                               │                                       │
       ┌───────────────────────┼───────────────────────┐               │
       ▼                       ▼                       ▼               ▼
┌──────────────┐      ┌──────────────────┐    ┌──────────────────┐  ┌─────────────────────┐
│ Document     │      │ Biometrics       │    │ Risk & Fraud     │  │ Human Review Triage │
│ Engine       │      │ Engine           │    │ Engine           │  │ Subsystem           │
├──────────────┤      ├──────────────────┤    ├──────────────────┤  ├─────────────────────┤
│ OpenCV Quality│     │ Face Detection   │    │ Signal Aggregation│ │ Case Routing        │
│ OCR Extract  │      │ 3D Liveness Check│    │ Rule Evaluator   │  │ Reviewer Locking    │
│ Tamper FFT   │      │ Face Match       │    │ Decision Matrix  │  │ Audit Logger        │
└──────────────┘      └──────────────────┘    └──────────────────┘  └─────────────────────┘
```

## Core Subsystems

### 1. Document Processing Subsystem
- **Quality Engine**: Runs OpenCV image processing algorithms (Laplacian variance for blur, luminance histogram analysis for glare, aspect boundary checks).
- **Classification & OCR**: Extracts fields from PAN, Aadhaar, Passport, DL, Voter ID using vendor-agnostic provider abstractions (`MockOCRProvider` or `RealAWSTextractOCRProvider`).
- **Tampering Engine**: Evaluates FFT frequency spectra for Moire patterns, screenshot metadata, and edge noise density.

### 2. Biometric Verification Subsystem
- **3D Face Liveness**: Runs interactive or passive motion challenges to block presentation attacks.
- **Face Comparison**: Calculates 128D facial feature embeddings to compute similarity distance between document photo and selfie.

### 3. Risk & Decision Engine
- Evaluates weighted penalties across Quality, OCR Confidence, Tamper Score, Liveness, Face Match, and Demographic field discrepancies.
- Outputs machine-readable decisions: `AUTO_APPROVE`, `MANUAL_REVIEW`, `REJECT`.
