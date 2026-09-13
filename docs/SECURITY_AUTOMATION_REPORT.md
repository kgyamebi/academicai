# Security Automation Report — AcademicCheck AI

Date: 2026-09-07

| Gate | In CI? | Blocks merge? |
| --- | --- | --- |
| SAST | ruff (lint, not a full SAST) | ruff yes |
| Tests isolation/billing/security | pytest | yes (cov floors) |
| pip-audit | yes | **no** (`\|\| true`) |
| npm audit | no | no |
| Secret scan (gitleaks) | no | no |
| DAST (ZAP) | no | no |
| Container scan | no | no |
| SBOM | no | no |

Added: `.github/workflows/security-scan.yml` — **fail-closed** pip-audit + npm audit when that workflow runs. It is **not** a passing scan artifact until GitHub shows green.

**FAIL** DevSecOps completeness (SEC-03, SEC-04). Isolation pytest in CI is the only strong automated security gate today.
