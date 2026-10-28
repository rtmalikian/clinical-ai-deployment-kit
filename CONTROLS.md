# Control library — HIPAA safeguards → implementation → evidence → test

> General engineering information, not legal advice and not a compliance certification. HIPAA citations are to 45 CFR Part 164, Subpart C (§§164.308–164.316). "Addressable" (§164.306(d)) does not mean optional — it means implement if reasonable, document why not, and implement an equivalent alternative where reasonable.

| HIPAA safeguard | Implementation pattern in this kit | Evidence artefact | Automated test / check |
|---|---|---|---|
| §164.308(a)(1) Risk analysis & risk management | Threat model (docs/THREAT_MODEL.md) reviewed each release; scanner output tracked as a risk register input | Threat model + scan report in `examples/` | Scanner run in CI |
| §164.308(a)(2) Assigned security responsibility | Name a security official in SECURITY.md for any real deployment | SECURITY.md contact section | Manual checklist (BAA_CHECKLIST.md) |
| §164.308(a)(3) Workforce clearance / access authorisation | SSO-only access, SCIM provisioning/deprovisioning from the IdP, RBAC least privilege | IdP provisioning logs; docs/RBAC.md | `tests/test_identity.py` SCIM deprovision test |
| §164.308(a)(4) Information access management | RBAC matrix enforced in code (`oidc.RBAC`) | RBAC.md + code review | RBAC unit tests |
| §164.308(a)(5) Security awareness training | Pilot training plan (PILOT.md) includes phishing/PHI handling module | Training completion log (template in PILOT.md) | Manual |
| §164.308(a)(6) Security incident procedures | Incident-response playbook + tabletop script (docs/INCIDENT_RESPONSE.md) | Completed tabletop record | Annual tabletop (manual) |
| §164.308(a)(7) Contingency plan | Automated backups + restore drill (`backup.py`), retention pruning | Restore-drill report (verified file hashes) | `test_backup_restore_roundtrip` |
| §164.308(a)(8) Evaluation | Scanner re-run on every material change; findings triaged | Dated scan reports | CI scanner step |
| §164.310(a) Facility access / §164.310(b–c) Workstation & device security | Deploy only on managed, encrypted devices/hosts; no PHI on personal devices | Deployment checklist in PILOT.md go-live gate | Manual |
| §164.310(d) Device & media controls | Encrypted media, secure disposal procedure in IR playbook | Disposal log template | Manual |
| §164.312(a)(1) Access control — unique user ID | OIDC `sub` / SAML NameID per user; no shared accounts | IdP user list | OIDC validation tests |
| §164.312(a)(2)(iv) Encryption (addressable) | TLS in transit; KMS/encrypted volumes at rest, documented in SECURITY.md | Scanner ENC-01/ENC-02 | Scanner |
| §164.312(b) Audit controls | Append-only audit log of access + actions, PHI payloads never logged | Audit-log sample + review cadence | Scanner AUDIT-01, PHI-01 |
| §164.312(c) Integrity | Backup manifest SHA-256 verification; verified-generation pattern in consuming apps | Restore verification output | Backup tests |
| §164.312(d) Person/entity authentication | OIDC JWT validation / SAML assertion validation (`oidc.py`, `saml.py`) | Identity tests | 23 identity tests |
| §164.312(e) Transmission security | HTTPS only, HSTS at proxy, no PHI over email/fax stubs | Scanner ENC-01 | Scanner |
| §164.316 Policies, procedures, documentation | This repo: CONTROLS.md, SECURITY.md, playbooks kept under version control with retention ≥6 years for a real covered deployment | Git history | Manual |

## SOC 2 mapping (Trust Services Criteria, summary)

| SOC 2 | Kit coverage |
|---|---|
| CC6.1 Logical access — authenticated, least privilege | OIDC/SAML, RBAC, SCIM |
| CC6.3 Access removal | SCIM deprovisioning |
| CC6.5 / CC6.7 Data protection & transmission | PHI-not-in-logs rule, TLS, encryption-at-rest documentation |
| CC7.1 System operations — reproducible builds | Dependency pinning check (DEP-01) |
| CC7.2 Monitoring / audit | Audit controls, scanner |
| CC7.3 / CC7.4 Incident response & recovery | IR playbook, backup/restore drill |
| CC8.1 Change management | Version-controlled controls, CI tests, signed commits in consuming projects |

A SOC 2 report can only be issued by a CPA firm after an observation period. Nothing in this kit is a SOC 2 attestation.

## BAA-readiness checklist
See docs/BAA_CHECKLIST.md.
