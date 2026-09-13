"""Prove pip-audit fail-closed: a known-vulnerable pin must fail the auditor.

Uses an isolated requirements snippet (Jinja2 2.10 / CVE-era), not the app lockfile.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        req = Path(tmp) / "bad-requirements.txt"
        req.write_text("jinja2==2.10\n", encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, "-m", "pip_audit", "-r", str(req), "--progress-spinner", "off"],
            capture_output=True,
            text=True,
        )
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    swallowed = bool(re.search(r"pip-audit[^\n]*\|\|\s*true", ci))
    failed = proc.returncode != 0
    payload = {
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "live_money": False,
        "deliberately_vulnerable": "jinja2==2.10",
        "pip_audit_exit_code": proc.returncode,
        "fail_closed": failed,
        "ci_pip_audit_swallowed": swallowed,
        "ok": failed and not swallowed,
        "stdout_tail": (proc.stdout or "")[-1500:],
        "stderr_tail": (proc.stderr or "")[-800:],
    }
    out = ROOT / "ops" / "cert_pip_audit_failclosed.json"
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: payload[k] for k in ("ok", "fail_closed", "pip_audit_exit_code", "ci_pip_audit_swallowed")}, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
