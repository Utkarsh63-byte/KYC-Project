# Threat Model & Security Mitigations

| Threat Vector | Impact | Likelihood | System Mitigation | Residual Risk |
| :--- | :--- | :--- | :--- | :--- |
| **Presentation Attack / Biometric Spoofing** | HIGH | MEDIUM | Active/Passive 3D Liveness Detection & depth pulse analysis | LOW |
| **Digital Screen Photograph / Tampering** | HIGH | HIGH | FFT Frequency Moire pattern analysis & Canny edge noise heuristics | LOW |
| **Cross-Tenant Data Leakage** | CRITICAL | LOW | Strict ORM `tenant_id` query scoping & middleware authorization guards | LOW |
| **Session Hijacking / Replay Attack** | HIGH | MEDIUM | Short-lived JWT tokens (60 min) & client IP binding | LOW |
| **Man-In-The-Middle / API Abuse** | HIGH | MEDIUM | TLS 1.3, Rate limiting, Request validation, WAF rules | LOW |
| **SQL Injection / XSS Attacks** | HIGH | LOW | SQLAlchemy parameterized queries & Pydantic strict schemas | NONE |
