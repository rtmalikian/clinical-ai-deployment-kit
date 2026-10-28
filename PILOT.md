# 90-day pilot playbook — forward-deployed delivery for a clinical AI tool

> **Honesty note:** The author has not run a real hospital pilot and has no AI customers. This is a playbook written from clinic-operations experience (running a direct primary care clinic) plus the engineering in this kit — and a *simulated* dry-run (`examples/simulation/`, stamped SIMULATED / SYNTHETIC DATA). It is not a case study and reports no real results.

## Phase 0 — Discovery (days 1–14)
- Stakeholder map: clinical sponsor, clinic operations lead, compliance/privacy officer, IT/security reviewer, payer-relations contact, front-line coordinators (end users), patient representative.
- Baseline measurement *before* anything is installed: sample 2 weeks of PA requests and record the metrics below by hand. No baseline, no pilot claim.
- Data-flow review: where PHI enters, lives, and leaves; BAA list (docs/BAA_CHECKLIST.md); security review packet = scanner report + threat model + SECURITY.md.
- Success criteria signed by the sponsor before build/config starts.

## Phase 1 — Sandbox (days 15–30)
- Deploy in a sandbox with synthetic data only (use the FHIR validation harness in this kit on Synthea-format bundles before touching any real feed).
- SSO wired to the organisation's IdP (OIDC or SAML), SCIM provisioning on, RBAC roles mapped to real job titles (docs/RBAC.md).
- Go-live gate: backup/restore drill passed, incident-response contacts named, training scheduled.

## Phase 2 — Shadow mode (days 31–60)
- Tool runs alongside the manual workflow; its outputs are *not* submitted. Coordinators log where it was right, incomplete, or wrong.
- Weekly review: disagreement log, safety issues triaged first, eval set grows from real (de-identified, approved) shadow cases.
- Exit criteria (example thresholds, set with sponsor): completeness-gate precision ≥0.90 on shadow cases, zero PHI-in-log incidents, coordinator acceptance ≥ agreed threshold.

## Phase 3 — Limited live (days 61–90)
- One service line / payer only, human review and signature on every submission, kill switch and rollback to manual workflow rehearsed.
- Metrics reported weekly against the Phase 0 baseline, with sample sizes — never percentages without denominators.

## Success metrics — definitions and measurement methods (no invented results)
| Metric | Definition | How measured |
|---|---|---|
| PA turnaround (clinic-side) | Hours from order signed to complete packet submitted | Timestamps in the case tracker; median + IQR, not just mean |
| First-pass completeness rate | Packets accepted as complete by the payer on first submission ÷ all first submissions | Payer responses logged per case |
| Coordinator time per PA | Active assembly minutes per case | Time sampling in shadow phase + tracker timestamps live |
| Clinician time saved | Clinician minutes on PA paperwork per week vs baseline | 1-week time diary at baseline and at day 90 |
| Safety / quality | Unsupported-claim rate, PHI incidents, escalations | Audit log review; any PHI incident pauses the pilot |

## Training plan
90-minute coordinator session, 30-minute clinician session, 15-minute PHI/security awareness module for everyone with access; super-user named per shift; refresher at day 60.

## Go-live checklist
SSO enforced · RBAC verified with test accounts · audit log reviewed · backup restored successfully in drill · IR playbook contacts current · BAA(s) executed where required · disclaimer/limitations briefed to users · rollback rehearsed.

## Simulated dry-run
`src/deployment_kit/simulate.py` runs these exact metric definitions over 90 days of seeded synthetic PA requests and writes `examples/simulation/SIMULATED_dashboard.md`. Every output is stamped SIMULATED / SYNTHETIC DATA — NOT A REAL PILOT. It proves the measurement code works end-to-end; it proves nothing about real-world efficacy.
