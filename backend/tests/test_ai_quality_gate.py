from app.services.ai.eval import load_baseline, run_all, suite_sizes, write_baseline


def test_evaluation_suite_has_1000_cases():
    sizes = suite_sizes()
    assert sizes["total"] >= 1000
    assert sizes["question"] >= 200
    assert sizes["thesis"] >= 20
    assert sizes["citation"] >= 20


def test_ai_quality_does_not_regress():
    metrics = run_all()
    baseline = load_baseline()
    if not baseline:
        write_baseline(metrics)
        baseline = load_baseline()
    by_name = {m.name: m for m in metrics}
    for name, previous in baseline.items():
        current = by_name[name].f1
        assert current + 0.03 >= previous, f"{name} F1 dropped from {previous} to {current}"
    # Launch floor for deterministic analyzers. Raise the committed baseline as suites improve.
    assert by_name["question_analyzer"].f1 >= 0.90
    assert by_name["citation_extractor"].f1 >= 0.70
    assert by_name["thesis_analyzer"].f1 >= 0.55
