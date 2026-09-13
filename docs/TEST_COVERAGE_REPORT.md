# Test Coverage Report — AcademicCheck AI

Date: 2026-09-07  
Command: `pytest -q --cov=app --cov-report=term`  
Result: **176 passed**, TOTAL **5657 statements, 1176 missed, 79%**.

CI floor: `--cov-fail-under=70` overall, `75` on billing/credits/deps. Target **90%**: **FAIL**.

| Package / module (selected) | Coverage |
| --- | ---: |
| `app.deps` | 80% |
| `app.services.credits` | 96% |
| `app.services.billing` | 60% |
| `app.services.auth` | 80% |
| `app.api.v1.reports` | 90% |
| `app.api.v1.public` | 53% |
| `app.services.ai.provider` | 57% |
| `app.services.documents.storage` | 55% |
| `app.workers.queue` | 58% |
| `app.workers.rq_worker` | 0% |
| **TOTAL** | **79%** |

This pass added `tests/test_engineering_quality.py` (count 166 → 176). TOTAL stayed **79%**. Do not treat extra tests as a coverage-gate pass.

Do not raise CI to `--cov-fail-under=90` until that run is green.

**FAIL** coverage certification at 90%.
