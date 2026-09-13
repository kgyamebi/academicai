"""Local heuristic analysis parallelism. Not a live-provider 10k-analysis certificate."""

from __future__ import annotations

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("APP_SECRET_KEY", "cert-secret")
os.environ.setdefault("JWT_SECRET_KEY", "cert-jwt-secret-key-32-bytes-min")

from app.services.ai.cache import cache_key, get_cached, reset_cache, set_cached  # noqa: E402
from app.services.ai.provider import AIResponse  # noqa: E402
from app.services.analysis.engine import run_analysis  # noqa: E402
from app.services.documents.extractor import ExtractedDocument, ExtractedParagraph  # noqa: E402

ESSAY = (
    "Globalization has changed trade in developing economies. This essay argues that the effects are mixed: "
    "export growth often rises, but inequality can widen unless industrial policy is strong. "
    "East Asian industrialisers used trade alongside policy (Rodrik, 2011)."
)


def extracted() -> ExtractedDocument:
    para = ExtractedParagraph(
        index=0,
        text=ESSAY,
        char_end=len(ESSAY),
        word_count=len(ESSAY.split()),
    )
    words = len(ESSAY.split())
    return ExtractedDocument(
        text=ESSAY,
        normalized_text=ESSAY,
        paragraphs=[para],
        sections=[],
        word_count=words,
        word_count_excl_references=words,
        word_count_excl_headings=words,
        paragraph_count=1,
        sentence_count=max(1, ESSAY.count(".")),
        page_count=1,
        language="en",
    )


def pct(samples: list[float], p: float) -> float:
    ordered = sorted(samples)
    return ordered[min(len(ordered) - 1, int((len(ordered) - 1) * p / 100))]


def main() -> int:
    reset_cache()
    doc = extracted()
    # warm one run so import/model cost is not in every sample
    run_analysis(doc, "", academic_level="undergraduate", citation_style="apa7")
    runs = {}
    for conc in (1, 10, 50, 100):
        samples: list[float] = []
        errors = 0

        def one() -> float:
            t0 = time.perf_counter()
            run_analysis(doc, "", academic_level="undergraduate", citation_style="apa7")
            return (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        with ThreadPoolExecutor(max_workers=conc) as pool:
            futs = [pool.submit(one) for _ in range(conc)]
            for fut in as_completed(futs):
                try:
                    samples.append(fut.result())
                except Exception:
                    errors += 1
        elapsed = time.perf_counter() - t0
        runs[str(conc)] = {
            "parallel": conc,
            "p50_ms": round(pct(samples, 50), 3) if samples else None,
            "p95_ms": round(pct(samples, 95), 3) if samples else None,
            "elapsed_s": round(elapsed, 3),
            "errors": errors,
            "throughput_per_min": round(conc / max(elapsed, 0.001) * 60, 1),
        }
    reset_cache()
    key = cache_key("cert-prompt", strong=False)
    set_cached(key, AIResponse("{}", "unit", "cache", 1))
    hits = 0
    t0 = time.perf_counter()
    for _ in range(1000):
        if get_cached(key) is not None:
            hits += 1
    cache_ms = (time.perf_counter() - t0) * 1000
    payload = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "engine": "heuristic_run_analysis",
        "runs": runs,
        "cache_1000_hits": hits,
        "cache_1000_ms": round(cache_ms, 3),
        "live_provider": False,
        "not_run": ["parallel_1000", "parallel_5000", "parallel_10000", "live_openai", "live_failover_load"],
    }
    out = ROOT / "ops" / "cert_ai_results.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
