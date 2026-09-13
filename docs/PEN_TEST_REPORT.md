# Penetration test report — AcademicCheck AI

Date: 2026-09-07  
**Result: FAIL.** No independent penetration test was executed against a deployed host.

Pytest isolation, webhook HMAC, refresh reuse, and upload guards are **not** a pentest.

## Scope that remains untested on a host

| ID | Attack | Lab (pytest) | Host |
| --- | --- | --- | --- |
| PEN-01 | Horizontal IDOR (assignments, documents, reports, PDF, share, compare, coach, payments) | Pass in `test_isolation.py` | **Not run** |
| PEN-02 | Vertical privilege (guest/student → admin) | Pass | **Not run** |
| PEN-03 | Unsigned / replayed Stripe, Paystack, Flutterwave | Pytest HMAC | **Not run** (no keys) |
| PEN-04 | Refresh reuse after rotation | Pass this pass (family revoke persisted) | **Not run** |
| PEN-05 | Share-token guessing / expiry | Partial unit | **Not run** |
| PEN-06 | Prompt injection on coach + enhance | Partial | **Not run** |
| PEN-07 | Auth bypass via cookie/CSRF | Partial | **Not run** |

## Retest

Commission an ASVS-aligned test on staging with production-like secrets. Until that report exists with no open High findings, pentest certification stays **FAIL**.
