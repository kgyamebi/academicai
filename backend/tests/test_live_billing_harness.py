"""Live billing harness safety — no provider calls, no charges."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_prepare_refuses_without_harness_arm():
    env = os.environ.copy()
    env.pop("LIVE_BILLING_HARNESS", None)
    env["LIVE_BILLING_USER_EMAIL"] = "nobody@example.com"
    env["LIVE_BILLING_PROVIDER"] = "stripe"
    result = subprocess.run(
        [sys.executable, str(ROOT / "ops" / "live_billing_prepare.py"), "--scenario", "success"],
        env=env,
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    assert result.returncode == 2
    assert "LIVE_BILLING_HARNESS" in (result.stderr + result.stdout)


def test_verify_unknown_session_fails(tmp_path):
    session = tmp_path / "s.json"
    session.write_text(
        '{"scenario":"success","payment_id":"00000000-0000-0000-0000-000000000001",'
        '"idempotency_key":"x","amount_cents":100,"credits_expected":"1",'
        '"baseline_credits_remaining":"0"}',
        encoding="utf-8",
    )
    env = os.environ.copy()
    # Use whatever DB the test suite uses; missing payment => FAIL not crash preferred
    result = subprocess.run(
        [sys.executable, str(ROOT / "ops" / "live_billing_verify.py"), "--session", str(session), "--out", str(tmp_path / "out.json")],
        env=env,
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    # Should exit non-zero (missing payment) or 0 only if somehow exists — assert not success pass
    assert "PASS" not in result.stdout or result.returncode != 0 or '"pass": true' not in (tmp_path / "out.json").read_text(encoding="utf-8")
