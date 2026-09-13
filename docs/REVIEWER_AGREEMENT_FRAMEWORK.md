# Reviewer-agreement framework

Date: 2026-09-07

**Lecturer agreement is unmeasured.** n=0. Do not claim it.

## Protocol

For every held-out document:

1. Reviewer A labels independently.
2. Reviewer B labels independently.
3. AcademicCheck AI label is recorded from the frozen analyzer version.
4. Append one JSON object to `backend/app/services/ai/reviewer_labels.jsonl`.

Schema: `reviewer_labels.schema.json` (`id`, `suite`, `reviewer_a`, `reviewer_b`, `ai`, `uncertain`).

## Metrics (`agreement.py`)

| Metric | Function |
| --- | --- |
| Pairwise % agreement | A–B, A–AI, B–AI |
| Cohen’s κ | A–B (human ceiling), A–AI, B–AI |
| Fleiss’ κ | A, B, AI as three raters |

Target for certification: **AI–human κ comparable to A–B κ**, not “AI agrees with itself”.

## Current report

```
n=0
cohen_a_b=null
fleiss=null
note: No dual reviewer labels are on disk.
```

Synthetic kappa unit tests use toy strings and are **not** lecturer results.

## Uncertainty

If either reviewer sets `uncertain=true`, the item is excluded from the primary κ table and listed in an uncertainty appendix.
