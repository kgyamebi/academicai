# Prompt Security Report — AcademicCheck AI

Date: 2026-09-07  
Every assignment is untrusted. Tests: `backend/tests/test_prompt_injection.py` (1000 cases asserted).

| Attack | Control | Evidence | Residual |
| --- | --- | --- | --- |
| Prompt injection | regex `looks_like_injection` | templates flagged | Novel phrasing |
| Instruction override | wrap_layers SYSTEM>USER>DOCUMENT | `test_document_layer_is_wrapped` | Model may still obey |
| System prompt disclosure | `sanitize_model_output` + leak markers | `test_secret_and_system_leak_are_rejected` | Incomplete marker list |
| Data extraction | untrusted wrappers | code | Residual |
| Citation fabrication | verify path `could_not_verify`, no invented title | isolation citation test | HTTP verify not live corpus |

Core heuristic analysis does not require the LLM. Enhance/coach can return None.

**PASS synthetic suite. FAIL** as a proof against a live frontier model (no live_provider).
