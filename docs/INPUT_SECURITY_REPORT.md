# Input Security Report — AcademicCheck AI

Date: 2026-09-07

| Channel | Control | Test | Residual |
| --- | --- | --- | --- |
| JSON bodies | Pydantic schemas | 422 tests | — |
| Query/path IDs | UUID + ownership | isolation | — |
| Headers | CSRF compare_digest; webhook HMAC | hardening / billing | CSRF exempt login |
| Uploads | MIME + magic + zip/pdf | document_security | ClamAV optional |
| Webhooks | signature + tolerance | billing_critical | live unrun |
| SQL | ORM parameters | no string-built tenant SQL in APIs | — |
| NoSQL | none | n/a | Redis keys app-controlled |
| Command | no shell on user input | — | — |
| Path traversal | storage `..` reject | storage tests | — |
| Header injection | no unsanitized Location from user | review | — |
| CSV | not a product export of formulas | — | — |
| SSTI | Jinja not used for user templates | — | — |
| Prompt | firewall + wrap_layers | test_prompt_injection 1000 cases | model residual |

**PASS repo input gates. FAIL** as a DAST certificate.
