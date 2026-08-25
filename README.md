# Digital KYC & Identity Verification Platform

> **Enterprise Bank-Grade Digital KYC, Biometric Liveness & Multi-Signal Verification Engine**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg?logo=react)](https://reactjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.2-3178C6.svg?logo=typescript)](https://www.typescriptlang.org)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.9-5C3EE8.svg?logo=opencv)](https://opencv.org)
[![AWS Ready](https://img.shields.io/badge/AWS-Textract_%7C_Rekognition-FF9900.svg?logo=amazon-aws)](https://aws.amazon.com)

---

## 📌 Product Overview

KryptonKYC is an enterprise-grade Digital KYC & Identity Verification platform designed for Banks, NBFCs, Fintechs, and Regulated Financial Institutions. It delivers automated remote customer onboarding with real-time document quality checking, OCR data extraction, digital tamper detection, 3D face liveness verification, facial matching, multi-signal risk scoring, human-in-the-loop review triage, and immutable security auditability.

---

## 🚀 Key Platform Capabilities

1. **Intelligent Document Pipeline**: Automated auto-classification for PAN, Aadhaar, Passport, Driving License, Voter ID.
2. **Real-Time Quality Engine**: OpenCV-powered Laplacian blur variance, luminance glare detection, and resolution verification.
3. **Fraud & Tamper Analysis**: FFT frequency Moire pattern analysis, digital screenshot indicators, edge noise inspection.
4. **Biometric Face Verification**: Active/Passive 3D Liveness verification and facial landmark feature comparison.
5. **Multi-Signal Risk Engine**: Dynamic scoring matrix generating explainable decision outcomes (`AUTO_APPROVE`, `MANUAL_REVIEW`, `REJECT`).
6. **Human-in-the-Loop Triage**: Split-screen reviewer portal with field ROI highlighting and audit trail tracking.
7. **Executive Demo Sandbox**: 1-click scenario trigger simulating clean pass, blur, worn ID, spoof attack, face mismatch, and screen tampering.
8. **PDF Report Engine**: Downloadable cryptographically hashed KYC Verification Certificates.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2.0 (Async), AsyncPG / Aiosqlite, OpenCV, PIL, ReportLab, Pydantic v2
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS v3, Lucide Icons, Framer Motion
- **Database**: PostgreSQL (Multi-Tenant, UUID keys) & Redis
- **Cloud & AI**: AWS Textract (OCR), AWS Rekognition (Face Liveness & Matching), AWS S3 (WORM Object Lock), AWS KMS
- **DevOps**: Docker, Docker Compose, Terraform IaC

---

## ⚡ Quick Start (Local Docker Execution)

```bash
# 1. Clone Repository
git clone https://github.com/enterprise-kyc/kyc-platform.git
cd KYC-Project

# 2. Launch Full Stack with Docker Compose
docker compose up --build
```

Access Applications:
- **Customer KYC Portal & Demo**: [http://localhost:3000](http://localhost:3000)
- **FastAPI Interactive Swagger Specs**: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)

---

## 📚 Technical Documentation

- 📐 [Architecture Documentation](docs/ARCHITECTURE.md)
- 🔒 [Security & Compliance](docs/SECURITY.md)
- 🌐 [API Reference Specification](docs/API.md)
- 🗄️ [Database Schema & Multi-Tenancy](docs/DATABASE.md)
- 🤖 [AI/ML Pipeline & Risk Scoring](docs/AI_ML.md)
- ⚠️ [Threat Model & Mitigations](docs/THREAT_MODEL.md)
- 📜 [Regulatory Compliance Readiness](docs/COMPLIANCE.md)
- 🚢 [AWS Infrastructure & Deployment](docs/DEPLOYMENT.md)
