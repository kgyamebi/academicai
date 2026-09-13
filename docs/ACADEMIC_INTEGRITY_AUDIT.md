# Academic Integrity Audit — AcademicCheck AI

Date: 2026-09-07

## Misconduct promotion
**PASS.** Product is a checker, not a generator. No “write my assignment” CTA. Coach disclaimer: will not write the assignment (`coach.py`).

## Does not generate full assignments
**PASS.** No generator endpoint. Improve modes are sentence/guidance; `improved_sentence` is unused (does not auto-rewrite papers).

## Does not fabricate references / citations / statistics / quotations
**PASS with residual.**  
- System prompt forbids invention (`provider.py`).  
- `verify_reference` returns `could_not_verify` and never invents a match (`test_verification_never_invents_on_empty`).  
- Hallucination suite / firewall tests.  
Residual: heuristic “example” teaching notes are generic, not sourced papers. Citations page tells users not to invent replacements.

## Disclaimers

| Surface | Present | Evidence |
| --- | --- | --- |
| Overall / grade | Yes | Report + PDF + `i18n.ts` + workflow test |
| Rubric | Yes | Engine label “AI-assisted rubric assessment — not an official grade”; help topic |
| AI-writing indicator | Yes | “Never interpret as definitely used AI”; no false-precision % |
| Citation verification | Yes | Help FAQ; citations page; engine teaching note mismatch ≠ fabricated |
| Institutional policy | Yes | Landing/footer trust string |

## Integrity FAIL/PARTIAL
- REQ-92 human QC: **FAIL** (empty reviewer file).  
- Marketing must not claim human-validated AI or guaranteed marks.

**Integrity launch subset:** satisfied for copy and non-generation. **Not** satisfied as “human-reviewed AI quality.”
