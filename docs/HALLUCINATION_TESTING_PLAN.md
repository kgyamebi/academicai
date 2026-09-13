# Hallucination testing plan

Date: 2026-09-07  
Source: `eval_report.json` → `hallucination_redteam`

## Guard

`allow_model_text` rejects model output when citation-like spans, DOIs, page locators, percentages, long quotes, journal-name stems, lecturer-expectation phrases, or fabricated-study phrases **do not appear** in the student text plus diagnostic.

## Suites

| Suite | n | Role | Result |
| --- | ---: | --- | --- |
| Unit cases `HALLUCINATION_CASES` | 4 | Regression | F1 1.00; CI low 0.51 |
| Red-team `hallucination_suite.py` | 1214 total / **1210 should-block** | Adversarial combinatorial | **escape 0 / 1210 = 0%** |
| Live LLM enhance/coach | 0 | Production hallucination rate | **not measured** |

Red-team covers fabricated authors/journals, percentages, DOIs, page numbers, quotations, unpublished studies, and “your lecturer expects…”.

`pass_target` for red-team (n≥1000 and escape <0.5%) is **true** on this combinatorial suite. That is **not** live-traffic certification. Models can hallucinate in ways the regex list does not list.

## Target for 98-path certification

Hallucination escape **< 0.5%** on:

1. The frozen 1000+ adversarial set (currently 0% escaped), **and**
2. 1000 live-provider outputs on held-out documents, counted by human adjudication of invented facts.

Until (2) exists, the certification gate `schema_compliance_live` / live hallucination rate remains **fail**.
