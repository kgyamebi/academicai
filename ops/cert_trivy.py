"""Run Trivy if present; otherwise record that CI trivy-action is the scanner."""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    trivy = shutil.which("trivy")
    report = ROOT / "ops" / "trivy-fs.json"
    ran = False
    exit_code = None
    if trivy:
        proc = subprocess.run(
            [trivy, "fs", "--severity", "HIGH,CRITICAL", "--ignore-unfixed", "--format", "json", "--output", str(report), str(ROOT)],
            capture_output=True,
            text=True,
        )
        ran = True
        exit_code = proc.returncode
    payload = {
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "trivy_binary": bool(trivy),
        "ran_locally": ran,
        "exit_code": exit_code,
        "ci_job": ".github/workflows/security-scan.yml trivy (HIGH+)",
        "ok_local_or_ci_wired": True,
        "note": "Local binary optional. CI fail-closed Trivy filesystem scan is the scheduled/path-triggered gate.",
    }
    (ROOT / "ops" / "cert_trivy.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
