# Payment Certification

Date: 2026-09-09

| Provider | Keys present | Live success | Live fail | Refund | Partial refund | Cancel | Expire | Duplicate webhook | Invalid signature | Sub create/cancel/renew | Credit purchase/refund |
| --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Stripe | No | Not run | Not run | Not run | Pytest only | Pytest | Pytest | Pytest | Pytest | Pytest | Pytest |
| Paystack | No | Not run | Not run | Not run | Pytest | Pytest | Pytest | Pytest | Pytest | Pytest | Pytest |
| Flutterwave | No | Not run | Not run | Not run | Pytest | Pytest | Pytest | Pytest | Pytest | Pytest | Pytest |

Go-live requirement “all providers pass live” → **FAIL**. Sandbox signatures/replay/refunds: **PASS** pytest.

