# REST API Reference Specification

Base URL: `/api/v1`

## Customer Endpoints

### 1. Create KYC Session
- **POST** `/kyc/sessions`
- **Request Body**:
```json
{
  "full_name": "Rahul Sharma",
  "email": "rahul@example.com",
  "phone": "+91 9876543210",
  "dob": "15/08/1992",
  "address": "Bengaluru, Karnataka"
}
```
- **Response**: `200 OK` (KYCSessionResult object)

### 2. Submit Privacy Consent
- **POST** `/kyc/sessions/{sessionId}/consent`
- **Request Body**:
```json
{
  "purpose": "Digital Identity Verification for Bank Account Onboarding",
  "policy_version": "v2.1",
  "consent_granted": true
}
```

### 3. Upload Identity Document
- **POST** `/kyc/sessions/{sessionId}/documents` (multipart/form-data)
- **Form Fields**: `doc_type` ("PAN" | "AADHAAR" | "PASSPORT" | "DRIVING_LICENSE"), `file` (Binary Image/PDF)

### 4. Verify Biometric Face Liveness
- **POST** `/kyc/sessions/{sessionId}/liveness`
- **Request Body**:
```json
{
  "selfie_base64": "data:image/jpeg;base64,..."
}
```

### 5. Execute Risk & Decision Engine
- **POST** `/kyc/sessions/{sessionId}/verify`
- **Response**: Risk Evaluation Result with explainable decision reasons.

### 6. Download PDF Verification Certificate
- **GET** `/kyc/sessions/{sessionId}/report/pdf`
- **Response**: `application/pdf` binary stream.
