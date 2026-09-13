"""Local nginx cache standing in for a CDN. Proves headers + HIT/MISS, not Cloudflare."""

from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CDN = "http://127.0.0.1:18081"
ORIGIN = "http://127.0.0.1:18001"


def fetch(url: str) -> tuple[int, dict[str, str], bytes]:
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=10) as resp:
        headers = {k.lower(): v for k, v in resp.headers.items()}
        return resp.status, headers, resp.read()


def main() -> int:
    payload: dict = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "cdn_standin": CDN,
        "origin": ORIGIN,
        "live_cdn_account": False,
        "not_reached": [],
    }
    try:
        status, headers, body = fetch(f"{ORIGIN}/api/public/faqs")
        payload["origin"] = {
            "status": status,
            "cache_control": headers.get("cache-control"),
            "cdn_cache_control": headers.get("cdn-cache-control"),
            "surrogate_key": headers.get("surrogate-key"),
            "bytes": len(body),
        }
        first = fetch(f"{CDN}/api/public/faqs")
        time.sleep(0.3)
        second = fetch(f"{CDN}/api/public/faqs")
        payload["nginx_cache"] = {
            "first_status": first[0],
            "first_x_cache": first[1].get("x-cache-status"),
            "second_status": second[0],
            "second_x_cache": second[1].get("x-cache-status"),
            "hit_on_second": (second[1].get("x-cache-status") or "").upper() == "HIT",
        }
        priv = fetch(f"{ORIGIN}/api/live")
        payload["private_live"] = {
            "cache_control": priv[1].get("cache-control"),
            "no_store": priv[1].get("cache-control") == "no-store",
        }
    except Exception as exc:
        payload["error"] = str(exc)
        payload["not_reached"].append("nginx_cdn_standin")
    out = ROOT / "ops" / "cert_cdn_cache.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if "error" not in payload else 1


if __name__ == "__main__":
    raise SystemExit(main())
