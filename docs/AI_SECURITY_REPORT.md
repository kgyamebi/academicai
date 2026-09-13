# AI Security Report — AcademicCheck AI

Date: 2026-09-09  
Evidence: `test_prompt_injection.py`, firewall + `wrap_layers`.

| Threat | Mitigation | Proven? |
| --- | --- | --- |
| Prompt injection / override | SYSTEM > USER > DOCUMENT > REFERENCE | Synthetic PASS (≥1000 cases historical) |
| Prompt leakage | Output sanitizer | Partial |
| Tool abuse | No general tools in user context | Code |
| Data exfil via model | Residual model risk | Uneliminable |

Document text never placed in system layer.

**PASS synthetic AI security.** **FAIL** live red-team / live provider injection drill.
