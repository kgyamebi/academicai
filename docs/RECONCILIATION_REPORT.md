# Reconciliation Report — AcademicCheck AI

Date: 2026-09-09  

## System

- `ops/run_billing_reconcile.py` / `reconcile_billing.py`
- `billing_reconcile.reconcile_against_provider_snapshot`
- GHA `billing-reconcile.yml` (fail-closed without snapshot)
- Alert `billing_reconcile_mismatch`

## Detects

missing_internal · missing_provider · amount/currency/status mismatch · missing_success_txn

## Evidence

`test_billing_reconcile_alert.py`, sandbox S8.

**PASS** snapshot reconcile tooling. **FAIL** live provider API pull reconcile.
