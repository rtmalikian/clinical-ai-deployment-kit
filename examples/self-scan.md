# Compliance-as-code self-assessment — /home/hatch/workspace/work/clinical-ai-deployment-kit

**Score: 110/120 (92%)** across 12 controls · Files scanned: 32 · Secret hits: 0

> This is an automated self-assessment of engineering artefacts in code. It is **not** HIPAA certification, **not** a SOC 2 attestation, and **not** a substitute for a formal risk analysis (45 CFR 164.308(a)(1)) or independent audit.

| Control | Status | HIPAA (45 CFR) | SOC 2 | Matched pattern / evidence |
|---|---|---|---|---|
| AUTH-01 Authentication present | **PASS** | 164.312(d) Person or entity authentication | CC6.1 | \bauthenticate\b<br>oauth2|openid|oidc|saml<br>jwt|jose|bearer token<br>login_required|requires_auth|security\s*=|Depends\(.*(?:auth|current_user|get_current) |
| AUDIT-01 Audit logging | **PASS** | 164.312(b) Audit controls; 164.308(a)(1)(ii)(D) Information system activity review | CC7.2 | audit[_ ]?log|audit trail<br>logging\.(?:basic)?config|getlogger|structlog|access[_ ]log |
| ENC-01 Encryption in transit (TLS) configured or documented | **PASS** | 164.312(e)(1) Transmission security | CC6.7 | ssl|tls|https://|certbot|acme<br>hsts|strict-transport |
| ENC-02 Encryption at rest addressed | **PASS** | 164.312(a)(2)(iv) Encryption and decryption (addressable) | CC6.1 | encrypt(?:ion)? at rest|kms|aes-?256|encrypted volume|luks|sqlcipher |
| SEC-01 No hard-coded secrets in source | **PASS** | 164.312(a)(1) Unique user identification / access control; 164.308(a)(3) Workforce access | CC6.1 | — |
| DEP-01 Dependencies pinned / lockfile present | **WARN** | 164.308(a)(8) Evaluation; 164.316(b) Documentation | CC7.1 / CC8.1 | — |
| DOC-01 SECURITY.md present | **PASS** | 164.316(a) Policies and procedures; 164.308(a)(6) Security incident procedures | CC7.3 | SECURITY.md |
| BAK-01 Backup / retention / contingency addressed | **WARN** | 164.308(a)(7) Contingency plan; 164.310(d)(2)(iv) Data backup plan | CC7.4 | backup|retention|restore drill|disaster recovery|contingency plan |
| PHI-01 No PHI-like identifiers written to logs | **PASS** | 164.312(b) Audit controls; 164.502(b) Minimum necessary | CC6.5 | — |
| SEC-02 .gitignore excludes .env / secrets | **PASS** | 164.308(a)(3)(ii)(C) Emergency access / access establishment | CC6.1 | .gitignore:.env |
| RBAC-01 Role-based access control addressed | **PASS** | 164.312(a)(2)(i) Unique user identification; 164.308(a)(4) Information access management | CC6.3 | rbac|role[-_ ]based|\broles?\b.*(?:admin|clinician|auditor)|permission |
| IR-01 Risk analysis / incident response documented | **PASS** | 164.308(a)(1)(ii)(A) Risk analysis; 164.308(a)(6) Security incident procedures | CC7.3/CC7.4 | incident response|risk analysis|risk assessment|threat model |

## Remediation for non-pass controls

- **DEP-01 Dependencies pinned / lockfile present (warn):** Pin exact versions (==) or commit a lockfile so builds are reproducible and auditable.
- **BAK-01 Backup / retention / contingency addressed (warn):** Automate backups, define retention, and run a documented restore drill (see backup.py).
