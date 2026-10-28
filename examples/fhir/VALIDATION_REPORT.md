# FHIR R4 validation report

**Data provenance:** LOCALLY GENERATED synthetic FHIR R4 bundle (generated 2026-10-28 by src/deployment_kit/fhir_gen.py, seed 42, 25 synthetic patients). NOT Synthea data and NOT real patients: a public Synthea sample download was attempted on 2026-10-28 and failed in this sandbox (empty reply from synthea.mitre.org), so the offline generator was used and is labelled as such. Format follows FHIR R4 resource shapes.

**Total resources:** 125

| Resource type | Count |
|---|---|
| Claim | 25 |
| Condition | 25 |
| Encounter | 25 |
| Observation | 25 |
| Patient | 25 |

## Data-quality findings

- Missing required fields: 1
- Missing patient family names: 1
- Implausible birth dates: 1
- Bad ICD-10 formats: 0
- Bad LOINC formats: 0
- Broken references: 0
- Total issues listed: 3

## Issues

- Patient/pat-003: missing family name
- Patient/pat-007: implausible birthDate 1899-01-01
- Condition/cond-011: coding missing 'code'

> Scope: structural, terminology-format and plausibility checks only. Not a substitute for the official HL7 FHIR validator or profile conformance testing against US Core / Da Vinci PAS.
