# Threat model (STRIDE) — clinical LLM application

Scope: a self-hosted clinical LLM workflow app (e.g. prior-auth drafting) with an embedded OpenAI-compatible gateway, SSO, audit log, and FHIR export. Method: STRIDE per element, reviewed per release (§164.308(a)(1) risk-analysis input). General information, not a formal risk analysis for any specific deployment.

| Threat | Example in this system | Mitigation in kit / consuming app |
|---|---|---|
| **S**poofing | Stolen session / forged token used to open cases | OIDC/SAML validation (signature, issuer, audience, expiry) in `oidc.py`/`saml.py`; short token lifetimes; no shared accounts (§164.312(d)) |
| **T**ampering | Edited audit log hides access; altered PA packet | Append-only / hash-verified audit trail; backup SHA-256 manifests (`backup.py`); verified generation — packet claims must quote the source note |
| **R**epudiation | User denies submitting a packet | Per-user identity (`sub`/NameID) on every action in the audit log (§164.312(b)) |
| **I**nformation disclosure | PHI in logs, prompts sent to an external LLM, secrets in code | PHI-not-in-logs scanner rule (PHI-01); redaction gate before any upstream call; secrets scanner (SEC-01); TLS (§164.312(e)); local/self-hosted model option keeps PHI on premises |
| **D**enial of service | Gateway flooded; IdP outage locks clinic out | Rate limiting at proxy; documented downtime procedure — manual workflow remains the fallback (contingency plan §164.308(a)(7)) |
| **E**levation of privilege | Coordinator account approves its own submissions | RBAC separation (coordinator write, clinician approve), SCIM deprovisioning on role change/departure (docs/RBAC.md) |

LLM-specific additions: prompt injection in pasted notes (treat note text as untrusted data, never instructions; verified generation drops unsupported claims), model output hallucination (completeness gate + human signature — output is never auto-submitted), and training-data leakage (no PHI is used for training in this architecture).

Residual risks stated plainly: a self-hosted deployment inherits the security of its host; this model does not cover insider misuse by an authorised user beyond audit deterrence, nor IdP compromise.
