# Supply Chain Security Report — AcademicCheck AI

Date: 2026-09-07

| Control | Status | Evidence |
| --- | --- | --- |
| Python deps | requirements.txt | CI install |
| pip-audit | **non-blocking** `\|\| true` | `.github/workflows/ci.yml` |
| npm | `npm ci \|\| npm install` | frontend CI |
| npm audit | **not in CI** | — |
| SBOM | **not generated** | — |
| Version pinning | mixed (requirements may float) | file |
| Docker image scan | **not run** | no Trivy job |
| License audit | **not run** | — |
| GitHub Actions | checkout@v4, setup-python@v5 | pin major, not SHA |
| Third parties | Stripe/Paystack/FLW/LLM/S3 | keys absent |

Workflow `security-scan.yml` (this pass) is fail-closed **when run**; it does not replace unsigned pentest.

**FAIL** supply-chain certification (SEC-03, SEC-04).
