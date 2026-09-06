# AI quality evaluation

Measured 6 Sep 2026 on the in-repo gold set.

| Suite | Cases | Precision | Recall | F1 | CI floor |
| --- | ---: | ---: | ---: | ---: | ---: |
| Question analyzer | 3240 | 1.000 | 1.000 | 1.000 | 0.90 |
| Thesis analyzer | 3360 | 1.000 | 1.000 | 1.000 | 0.95 |
| Citation extractor | 55 | — | — | 0.963 | 0.90 |
| Argument analyzer | 3040 | 1.000 | 1.000 | 1.000 | 0.95 |
| Evidence analyzer | 2400 | — | — | 0.996 | 0.95 |
| Rubric checker | 80 | 1.000 | 1.000 | 1.000 | 0.95 |
| **Total** | **10375** | | | | |

Gold covers undergraduate, postgraduate, masters, and PhD stems across humanities, business, engineering, healthcare, and economics.

## What these numbers are

Labels are **expert-constructed from writing-centre rules** that the production classifiers implement (`classify_thesis`, `has_reasoned_argument`, `needs_citation`, `rubric_covered`). CI fails if F1 drops more than 0.03 from `eval_baseline.json` or falls below the floors above.

Confusion matrices are attached to each `Metric` (`strong/weak/missing` for thesis; tp/fp/fn/tn for argument and evidence).

## What these numbers are not

- Not third-party human review
- Not a measurement of the optional LLM enhancement path
- Not proof that a lecturer would assign the same labels

Do not treat 1.00 F1 as “the AI is solved.” It means the deterministic analyzers are consistent with the stated rules on this gold set.
