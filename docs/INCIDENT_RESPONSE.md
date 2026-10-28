# Incident-response playbook + tabletop exercise

Supports §164.308(a)(6) security incident procedures and §164.318 / §§164.400–414 breach notification duties for a real covered deployment. Template — fill in named people before any real use.

## Severity
- **SEV-1:** confirmed/suspected PHI disclosure, ransomware, active intrusion.
- **SEV-2:** vulnerability in an internet-facing component, lost encrypted device.
- **SEV-3:** phishing attempt caught, scanner finding, near miss.

## First 60 minutes (SEV-1)
1. Declare: incident lead named, start a timestamped log (facts only).
2. Contain: isolate affected host/accounts, revoke tokens, disable SCIM-provisioned access if IdP is implicated — do not wipe evidence.
3. Notify: security official + privacy officer immediately; leadership within the hour.
4. Preserve: snapshots/logs copied to write-once storage.

## First 72 hours
Risk assessment per §164.402 (nature/extent of PHI, who received it, whether actually viewed, mitigation). Breach notification analysis under §§164.404–410 (individuals, HHS, media if ≥500 in a state) — deadlines are legal duties; get counsel involved early. Document everything per §164.316(b)(2)(i) (retain 6 years).

## Tabletop exercise (run annually, ~60 min)
**Scenario:** A coordinator reports that a PA packet PDF was emailed to the wrong payer contact, and the audit log shows an unknown IP used a clinician's SSO account the same morning.
Prompts: Who declares SEV? What do you revoke first, and what breaks clinically? How do you establish whether the packet was opened? Who drafts the §164.402 four-factor assessment? What is said to the clinic sponsor, and when?
**Pass criteria:** incident lead named in <5 min, containment steps ordered correctly, notification duties identified with owners, exercise gaps logged as actions with dates.
Record: date, participants, gaps, actions — filed as the §164.308(a)(6)(ii) response-and-reporting evidence artefact.
