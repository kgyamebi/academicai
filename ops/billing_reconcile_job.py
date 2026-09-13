"""Run offline billing reconcile and alert on mismatches. Does not call live PSPs."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.core.alerting import fire_alert  # noqa: E402
from app.services.billing_reconcile import reconcile_against_provider_snapshot  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", required=True, help="JSON array of provider txns")
    parser.add_argument("--out", default=str(ROOT / "ops" / "cert_billing_reconcile.json"))
    parser.add_argument("--alert", action="store_true", help="Fire alert when mismatches > 0")
    args = parser.parse_args()

    snapshot = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    with Session(engine) as db:
        result = reconcile_against_provider_snapshot(db, snapshot)
    engine.dispose()

    report = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ok": bool(result.get("ok")),
        "mismatch_count": int(result.get("mismatch_count") or 0),
        "result": result,
        "alerted": False,
    }
    if args.alert and report["mismatch_count"] > 0:
        report["alerted"] = fire_alert(
            "billing_reconcile",
            title="Billing reconcile mismatch",
            detail=f"{report['mismatch_count']} mismatches vs provider snapshot",
            severity="critical",
            context={"mismatch_count": report["mismatch_count"]},
        )
    Path(args.out).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"ok": report["ok"], "mismatch_count": report["mismatch_count"], "alerted": report["alerted"]}, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
