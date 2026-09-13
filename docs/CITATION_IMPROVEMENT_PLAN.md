# Citation improvement plan

Date: 2026-09-07  
Source: `eval_report.json`

## Measured (do not read as 98)

| Suite | n | P | R | F1 | F1 CI low |
| --- | ---: | ---: | ---: | ---: | ---: |
| Template citation (circular) | 55 | 1.000 | 1.000 | 1.000 | 0.935 |
| Held-out citation (independent) | 22 | 1.000 | 1.000 | 1.000 | **0.851** |
| Parser robustness (unlabeled) | 2440 | — | — | **not F1** | — |

Previous held-out F1 **0.933** (n=7, extra in-text/reference detections). After: skip citations inside References/Works Cited; do not treat ordinary sentences with a year as bibliography; Harvard and Chicago locators; two-author parentheticals in evidence classification.

**Not certified:** n=22, CI low 0.851 < 0.98.

## Styles supported in the extractor

APA 7, MLA 9, Harvard, Chicago author-date, IEEE numeric. Mixed-style documents are flagged, not silently “fixed”.

## Remaining work for 0.98+ **with evidence**

1. 2000 **labeled** excerpts: real, malformed, incomplete, mixed, repeated — double-annotated.
2. Reference matching: author normalisation, et al., year suffixes (2011a).
3. Live verification precision/recall on a DOI-labeled set via Crossref/OpenAlex/Semantic Scholar. Never mark `verified` without a provider match.
4. Keep the unlabeled 2440-case robustness suite as crash/regression only.

## Verification workflow (implemented, unscored)

Reference → lookup → candidate → confidence → **user review**. Statuses: `verified`, `likely_match`, `needs_review`, `could_not_verify`. Empty or failed lookup is `could_not_verify`. Precision = **null**.
