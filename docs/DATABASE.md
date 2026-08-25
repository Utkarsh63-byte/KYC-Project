# Database Schema & Data Architecture

## ER Diagram Entities

- `tenants` (id, name, code, webhook_url, webhook_secret, is_active, created_at, updated_at)
- `users` (id, tenant_id, email, hashed_password, full_name, role, is_active, created_at, updated_at)
- `customers` (id, tenant_id, external_customer_id, full_name, email, phone, dob, address, created_at)
- `kyc_sessions` (id, tenant_id, customer_id, status, risk_score, risk_level, decision, decision_reasons, ip_address, user_agent, created_at)
- `consent_records` (id, kyc_session_id, purpose, policy_version, consent_granted, ip_address, created_at)
- `documents` (id, kyc_session_id, doc_type, file_path, quality_score, quality_checks, tamper_score, tamper_checks, created_at)
- `extracted_fields` (id, document_id, field_name, field_value, confidence, source, validation_status)
- `biometric_checks` (id, kyc_session_id, liveness_score, liveness_status, face_match_score, face_match_status, selfie_image_path)
- `risk_assessments` (id, kyc_session_id, overall_risk_score, risk_level, recommended_action, risk_signals)
- `review_cases` (id, kyc_session_id, tenant_id, reviewer_id, status, reasons, reviewer_notes, decision)
- `audit_logs` (id, tenant_id, actor_id, actor_type, action, resource_type, resource_id, correlation_id, result, metadata_json, created_at)

## Indexes & Isolation
- B-Tree composite index on `(tenant_id, created_at)` across transactional tables.
- Foreign key constraints with cascade delete on child entities.
- Mandatory `tenant_id` filtering enforced at ORM layer.
