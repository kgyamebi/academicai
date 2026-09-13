"""CLI: reconcile internal ledger vs provider snapshot JSON; alert on mismatch.

Does not call live PSP APIs. Operators export sandbox/live dashboard JSON.

Usage:
  PYTHONPATH=backend py -3 ops/run_billing_reconcile.py --snapshot path/to/export.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.services.billing_reconcile import reconcile_against_provider_snapshot  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", required=True, help="JSON list of provider txns")
    parser.add_argument("--out", default=str(ROOT / "ops" / "cert_billing_reconcile.json"))
    parser.add_argument("--alert", action="store_true", help="Fire alert if mismatches")
    args = parser.parse_args()

    snapshot = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    if isinstance(snapshot, dict):
        snapshot = snapshot.get("transactions") or snapshot.get("items") or []
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    with Session(engine) as db:
        report = reconcile_against_provider_snapshot(db, snapshot)
    engine.dispose()

    if args.alert and not report.get("ok"):
        from app.core.alerting import fire_alert

        fire_alert(
            "billing_reconcile_mismatch",
            title="Billing ledger reconciliation mismatch",
            detail=f"mismatch_count={report.get('mismatch_count')} checked_internal={report.get('checked_internal')}",
            severity="critical",
            context={"mismatches": (report.get("mismatches") or [])[:10]},
            force=True,
        )

    Path(args.out).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"ok": report.get("ok"), "mismatch_count": report.get("mismatch_count"), "out": args.out}, indent=2))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
