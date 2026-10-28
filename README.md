> ## ⚠️ PROOF OF CONCEPT — NOT CLINICALLY TESTED
>
> **This tool has not been tested clinically and is a proof-of-concept for
> research and software demonstration only. It is not a medical device, it
> does not diagnose, treat, or rule out any condition, and its outputs may
> be wrong — including false positives and false negatives.**
>
> **Do not use it to make decisions about your health.**
> For any medical issue or concern, seek a licensed healthcare professional.
> **In an emergency, go to your nearest emergency room or dial 911 immediately.**

# Clinical AI Deployment Kit — HIPAA & SOC 2 Compliance-as-Code, FHIR Validation on Synthea-Format Data, SSO/SAML, and a 90-Day Pilot Playbook for Healthcare AI (FDE Kit)

**Healthcare AI deployment, HIPAA compliance-as-code, SOC 2 readiness, FHIR R4 validation, Synthea synthetic patient data, enterprise SSO (OIDC + SAML), SCIM provisioning, RBAC, backup/restore drills, incident response, SaMD/FDA CDS worksheet, and a forward-deployed-engineering (FDE) 90-day pilot playbook — in one open, test-covered kit.**

Built by [Raphael Malikian](https://github.com/rtmalikian) — healthcare founder/operator (bootstrapped and ran a direct primary care clinic as CEO) now building clinical AI in the open. Companion to [Prior-Auth Co-Pilot](https://github.com/rtmalikian/prior-auth-copilot) and Discharge Decoded.

## What this proves — and what it does NOT prove

**It proves** the author can build the deployment layer health AI employers ask for: a compliance scanner that audits a real repo (his own Prior-Auth Co-Pilot scores **100/120, 83%**, report in `examples/prior-auth-scan/`), working OIDC/SAML/SCIM identity code with tests, a FHIR R4 validator run on 125 real-format synthetic resources with a data-quality report, a tested backup/restore drill, and a pilot measurement pipeline that runs end-to-end on simulated data.

**It does NOT prove — read this before citing anything here:**
- **No real pilot has been run. The author has no AI customers and no hospital deployment.** `PILOT.md` is a playbook; `examples/simulation/` is a *simulated* dry-run on synthetic data, stamped as such on every file.
- **This kit does not make any system HIPAA compliant or SOC 2 certified.** Compliance is organisational and audited; this is engineering controls + checklists mapped to 45 CFR 164.308–316 and SOC 2 CC criteria.
- The FHIR bundle in `examples/fhir/` is **locally generated synthetic data in FHIR R4 / Synthea format** (a live Synthea sample download was attempted 2026-10-28 and failed in the build sandbox, so the offline generator was used and its provenance is labelled in the report). It is not Synthea's own output and contains no real patients.
- Simulation numbers are outputs of stated synthetic assumptions, **not results**.

## Components

| Component | What it does |
|---|---|
| `src/deployment_kit/scanner.py` | Compliance-as-code CLI: 12 controls (auth, audit logging, TLS, encryption at rest, secrets-in-code, dependency pinning, SECURITY.md, backup/retention, PHI-in-logs, RBAC…) scored, mapped to HIPAA + SOC 2, JSON + Markdown reports |
| `CONTROLS.md` | Control library: HIPAA safeguard → implementation pattern → evidence artefact → test, plus SOC 2 mapping and BAA-readiness summary |
| `src/deployment_kit/oidc.py` · `saml.py` · `app.py` | OIDC JWT validation, SAML assertion parsing/validation (documented stdlib limits), SCIM 2.0 provisioning stub, RBAC — FastAPI demo app |
| `src/deployment_kit/fhir_validate.py` · `fhir_gen.py` | FHIR R4 structural + terminology-format (LOINC / ICD-10) + data-quality validation; deterministic synthetic bundle generator |
| `src/deployment_kit/backup.py` | Backup with SHA-256 manifest + verified restore drill + retention pruning (§164.308(a)(7)) |
| `docs/` | STRIDE threat model, SaMD/FDA CDS worksheet, incident-response playbook + tabletop, BAA checklist, RBAC matrix |
| `PILOT.md` · `simulate.py` | 90-day FDE pilot playbook (discovery → sandbox → shadow → limited live) with metric definitions, and a seeded SIMULATED dry-run producing a dashboard |

## Real runs recorded in this repo
- **Scanner vs Prior-Auth Co-Pilot (2026-10-28, self-assessment): 100/120 (83%)**, 0 secret hits; WARN on encryption-at-rest documentation, dependency pinning, backup/contingency, risk/incident docs — see `examples/prior-auth-scan/`.
- **FHIR validation: 125 resources** (25 each Patient/Encounter/Condition/Observation/Claim), 3 data-quality issues found — exactly the 3 defects planted by the generator (missing family name, implausible 1899 birth date, missing condition code) — see `examples/fhir/VALIDATION_REPORT.md`.
- **Simulated pilot (SIMULATED / SYNTHETIC):** 926 synthetic PA requests over 90 days; first-pass completeness 71.4% → 93.8%, mean assembly 63.7 → 8.0 min under the stated synthetic assumptions — see `examples/simulation/SIMULATED_dashboard.md`.

## Quickstart
```bash
pip install -e ".[dev]"
pytest -q                                    # 49 tests
python -m deployment_kit.scanner /path/to/repo --md report.md --json report.json
python -m deployment_kit.simulate --out examples/simulation
uvicorn deployment_kit.app:app --port 8000   # identity demo (OIDC + SCIM)
```

## Tests
49 tests, all passing (scanner rules on compliant + deliberately non-compliant fixture repos, backup/restore round-trip, OIDC signature/expiry/issuer/audience/RBAC, SAML parsing/validation/tamper rejection, FHIR validators + planted-defect detection, simulation determinism + metric math, SCIM).

## License
MIT. Author: Raphael Malikian <rtmalikian@gmail.com> · [github.com/rtmalikian](https://github.com/rtmalikian) · [x.com/rtmalikian](https://x.com/rtmalikian)

*Keywords: HIPAA compliance, SOC 2, healthcare AI deployment, clinical AI, FHIR R4, Synthea, HL7, SSO, SAML, OIDC, SCIM, forward deployed engineer, FDE, prior authorization, compliance as code, SaMD, FDA CDS, threat model STRIDE.*
