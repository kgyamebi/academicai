#!/usr/bin/env python3
"""Thin alias: billing ledger reconcile (see ops/run_billing_reconcile.py)."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.argv[0] = str(ROOT / "ops" / "run_billing_reconcile.py")
raise SystemExit(runpy.run_path(str(ROOT / "ops" / "run_billing_reconcile.py"), run_name="__main__"))
