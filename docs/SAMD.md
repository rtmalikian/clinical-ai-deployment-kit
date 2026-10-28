# SaMD / FDA clinical decision support worksheet

> General information only — not legal or regulatory advice. Determinations depend on the specific product, claims, and intended use; a real product needs qualified regulatory counsel and, where relevant, an FDA pre-submission.

## The framework (summary)
Under the 21st Century Cures Act §3060 (FD&C Act §520(o)), some software functions are excluded from the device definition, including certain clinical decision support (CDS) for healthcare professionals. FDA's *Clinical Decision Support Software* guidance (final, September 2022) interprets the four statutory criteria. Software is generally **non-device CDS** only if it meets **all four**:

1. It does **not** acquire, process, or analyse a medical image, a signal from an IVD, or a pattern/signal from a signal acquisition system.
2. It displays, analyses, or prints medical information about a patient or other medical information (e.g. guidelines, peer-reviewed studies).
3. It **supports or provides recommendations** to a healthcare professional about prevention, diagnosis, or treatment — rather than providing a specific preventive/diagnostic/treatment directive or a definitive output.
4. It enables the healthcare professional to **independently review the basis** for the recommendation (sources, logic, data relied on are transparent), so the professional does not rely primarily on the software.

Software directed at **patients/consumers** (not HCPs), software that outputs a specific diagnosis/treatment directive, time-critical alarming software, or image/signal analysis software will generally fall on the **device** side and may need premarket review (e.g. 510(k)) as Software as a Medical Device (SaMD).

## Worksheet — answer for your product
| # | Question | If YES |
|---|---|---|
| 1 | Does it process medical images, signals, or IVD data? | Likely device — criterion 1 fails |
| 2 | Is any user a patient/consumer rather than an HCP? | CDS exclusion does not apply to patient-facing output |
| 3 | Does it give a specific directive ("order X", "this is Y") instead of options/recommendations? | Likely device |
| 4 | Can the HCP see and independently check every source, quote, and rule behind the output? | Required for non-device CDS |
| 5 | Is the output time-critical (deterioration alarms, triage-to-action)? | Likely device; higher risk class |
| 6 | Does marketing claim diagnosis/treatment benefit? | Claims define intended use — claims can make it a device |

## Worked example (author's own product, honestly)
Prior-Auth Co-Pilot drafts administrative prior-authorisation packets for clinician review and signature, with every claim quoted from the encounter note (criterion 4 pattern) and no diagnosis/treatment recommendation. On this worksheet that is administrative workflow software, not CDS about a clinical decision — but that is the author's reading for a proof-of-concept, not a regulatory determination, and any commercial version would need formal review before marketing claims are made.

## Risk thinking if it IS a device
IMDRF SaMD risk categorisation (significance of information × healthcare situation), IEC 62304 software lifecycle, ISO 14971 risk management, design controls (21 CFR 820.30), and clinical evaluation would apply. Budget for them before building, not after.
