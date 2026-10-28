# Security

## Scope and honest limits
This kit contains engineering controls, checklists and validation code for deploying clinical AI software. **It does not make any system HIPAA compliant or SOC 2 certified**, it is not a formal risk analysis for any specific organisation, and it is not legal, regulatory or medical advice. Compliance is organisational — policies, training, risk analysis, executed BAAs, and independent audit — of which code controls are only one part.

Component limits are documented where they live: `saml.py` (stdlib XML parsing limits — use a vetted SAML library in production), `oidc.py` (HS256 demo path — prefer RS256/JWKS in production), `app.py` (SCIM is an in-memory stub).

## Reporting a vulnerability
Email Raphael Malikian <rtmalikian@gmail.com> with details. Do not open a public issue for a security vulnerability. Acknowledgement target: 3 business days for this proof-of-concept project.

## Deployment security checklist (summary)
TLS everywhere · SSO enforced, no local passwords · RBAC least privilege · audit log on and reviewed · secrets in a secret manager, never in code · dependencies pinned · backups automated and restore-tested · incident contacts named. Full mapping: CONTROLS.md.
