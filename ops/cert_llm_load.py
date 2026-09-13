"""LLM analysis load. Heuristic is free and is run. Live provider spend is documented, not faked."""

from __future__ import annotations

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("APP_SECRET_KEY", "cert-secret")
os.environ.setdefault("JWT_SECRET_KEY", "cert-jwt-secret-key-32-bytes-min")

from app.services.analysis.engine import run_analysis  # noqa: E402
from app.services.documents.extractor import ExtractedDocument, ExtractedParagraph  # noqa: E402

ESSAY = (
    "Globalization has changed trade in developing economies. This essay argues that the effects are mixed: "
    "export growth often rises, but inequality can widen unless industrial policy is strong. "
    "East Asian industrialisers used trade alongside policy (Rodrik, 2011)."
)
TIERS = [int(x) for x in os.environ.get("CERT_LLM_HEURISTIC_TIERS", "1000,10000").split(",") if x.strip()]


def extracted() -> ExtractedDocument:
    para = ExtractedParagraph(index=0, text=ESSAY, char_end=len(ESSAY), word_count=len(ESSAY.split()))
    words = len(ESSAY.split())
    return ExtractedDocument(
        text=ESSAY,
        normalized_text=ESSAY,
        paragraphs=[para],
        word_count=words,
        word_count_excl_references=words,
        word_count_excl_headings=words,
        paragraph_count=1,
        sentence_count=max(1, ESSAY.count(".")),
        page_count=1,
        language="en",
    )


def main() -> int:
    doc = extracted()
    run_analysis(doc, "", academic_level="undergraduate", citation_style="apa7")
    payload: dict = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "heuristic": {},
        "live_provider": {
            "status": "not_run",
            "reason": "Requires live API spend (OpenAI/Anthropic/Gemini). Sandbox/test-mode provider 1k–10k is not free.",
            "gate": "HAL-16/HAL-17",
        },
        "not_reached": ["live_llm_1000", "live_llm_10000"],
    }
    for n in TIERS:
        errors = 0
        t0 = time.perf_counter()
        with ThreadPoolExecutor(max_workers=min(32, n)) as pool:
            futs = [
                pool.submit(
                    run_analysis,
                    doc,
                    "",
                    academic_level="undergraduate",
                    citation_style="apa7",
                )
                for _ in range(n)
            ]
            for fut in as_completed(futs):
                try:
                    fut.result()
                except Exception:
                    errors += 1
        elapsed = time.perf_counter() - t0
        payload["heuristic"][str(n)] = {
            "n": n,
            "errors": errors,
            "elapsed_s": round(elapsed, 3),
            "per_min": round(n / max(elapsed, 0.001) * 60, 1),
            "pass": errors == 0,
        }
        print(f"heuristic {n}: {payload['heuristic'][str(n)]}", flush=True)
    (ROOT / "ops" / "cert_llm_load.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"heuristic": payload["heuristic"], "not_reached": payload["not_reached"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
