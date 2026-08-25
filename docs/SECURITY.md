# Security & Encryption Architecture

## Security Controls Overview

### 1. Data Encryption
- **In Transit**: TLS 1.3 enforced across all API endpoints and web socket connections.
- **At Rest**: AES-256 KMS envelope encryption for documents and database storage. Sensitive PII fields (PAN, Aadhaar numbers) are encrypted prior to persistence.

### 2. Multi-Tenancy & Authorization
- Every query is scoped by `tenant_id`.
- Cross-tenant data access attempts trigger immediate 403 Forbidden exceptions and security audit logs.
- Role-Based Access Control (RBAC): `SUPER_ADMIN`, `TENANT_ADMIN`, `REVIEWER`, `CUSTOMER`.

### 3. API Security & Session Management
- Short-lived JWT bearer tokens (60 minutes default expiration).
- HMAC SHA-256 signatures on outward webhooks to prevent spoofing.
- OWASP Security Headers enforced on all responses (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security`).
