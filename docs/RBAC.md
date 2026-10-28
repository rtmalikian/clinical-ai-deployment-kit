# RBAC matrix + identity architecture

Enforced in code in `src/deployment_kit/oidc.py` (`RBAC`), provisioned via SCIM (`app.py`), authenticated via OIDC or SAML.

| Role | read | write | approve/submit | view audit | manage users |
|---|---|---|---|---|---|
| admin | ✓ | ✓ | ✓ | ✓ | ✓ |
| clinician | ✓ | ✓ | ✓ | — | — |
| coordinator | ✓ | ✓ | — | — | — |
| auditor | ✓ | — | — | ✓ | — |
| readonly | ✓ | — | — | — | — |

Design rules: least privilege by default; approval separated from drafting (a coordinator cannot approve their own packet); auditor is read-only by construction; access is provisioned and *removed* by the IdP via SCIM, never by local account creation; break-glass admin access is logged and reviewed (§164.312(a)(2)(ii) emergency access procedure).

## OIDC vs SAML — which to wire
OIDC for new deployments (simpler, JSON/JWT, the `oidc.py` path). SAML 2.0 when the customer's IdP or procurement requires it (many hospital systems) — use `saml.py` validation logic with a production XML-signature library (see its documented limits). Both land on the same claims → roles mapping, so the application code does not care which front door was used.
