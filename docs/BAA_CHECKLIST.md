# BAA-readiness checklist

A Business Associate Agreement (§§164.502(e), 164.504(e)) is required before PHI flows to any vendor/subcontractor in a real deployment. This checklist prepares an engineering org to sign one — it is not a BAA and not legal advice.

## Before you can credibly sign
- [ ] Named security official and privacy contact (§164.308(a)(2))
- [ ] Written risk analysis, current within 12 months (§164.308(a)(1))
- [ ] Access is SSO + RBAC, unique IDs, no shared accounts (§164.312(a))
- [ ] Audit logging on, reviewed on a cadence (§164.312(b))
- [ ] Encryption in transit everywhere; at-rest documented (scanner ENC-01/02 pass)
- [ ] Backup + tested restore (§164.308(a)(7))
- [ ] Incident-response playbook + named contacts; breach-notification duties understood (§§164.400–414)
- [ ] Workforce training records (§164.308(a)(5))
- [ ] Subcontractor inventory: every sub-processor listed, with their BAAs / security posture (cloud host, email, fax provider, LLM provider — a self-hosted/local model removes the LLM line entirely)
- [ ] Data-return / destruction on termination procedure (§164.504(j))
- [ ] Minimum-necessary data flows documented (what PHI, why, where it goes)

## Red flags in a counterparty's BAA
No breach-notification timeframe, carve-outs for their subcontractors, liability terms that make notification economically irrational, or refusal to name sub-processors. Escalate to counsel.
