# Architecture

```
 deployment target repo ──► scanner.py ──► scored report (JSON + Markdown)
                             HIPAA 164.308-316 / SOC 2 CC mapping

 identity:  IdP ──OIDC JWT──► oidc.py validate ──┐
            IdP ──SAML──────► saml.py validate ──┼─► claims → RBAC ─► app
            IdP ──SCIM──────► app.py /scim/v2 ───┘   (provision/deprovision)

 data:      FHIR R4 bundle ─► fhir_validate.py ─► data-quality report
 operations: source dir ─────► backup.py ─► tar.gz + SHA-256 manifest ─► restore + verify
 pilot:     PILOT.md metrics ─► simulate.py (seeded, synthetic) ─► SIMULATED dashboard
```

Components are deliberately stdlib-first: the scanner, backup, OIDC (HS256 path), SAML parser, FHIR validator and simulation run with no third-party packages, so a security reviewer can read everything the kit does. FastAPI is the only optional dependency, for the identity demo app.

Data flow rule that runs through every component: PHI payloads are never written to logs; identifiers in reports are structural (resource types, counts), not patient data. The FHIR bundles used in examples are synthetic.
