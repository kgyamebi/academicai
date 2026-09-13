"""AI evaluation harness: circularity, CIs, agreement, verification, red-team size."""

from app.services.ai.agreement import agreement_report, load_reviews
from app.services.ai.citation_corpus import citation_parser_cases, parser_robustness
from app.services.ai.eval import CERT_MIN_N, extras_bundle, run_all
from app.services.ai.hallucination_suite import build_hallucination_suite, hallucination_escape_rate
from app.services.ai.live_eval import live_eval_status
from app.services.ai.prompt_registry import regression_gate, registry_report
from app.services.ai.stats import cohen_kappa, fleiss_kappa, wilson_interval
from app.services.analysis.verify_sources import verify_reference


def test_template_suites_are_marked_circular_and_not_certifiable():
    metrics = {m.name: m for m in run_all()}
    for name in (
        "question_analyzer",
        "thesis_analyzer",
        "argument_analyzer",
        "evidence_analyzer",
        "citation_extractor",
        "rubric_checker",
    ):
        assert metrics[name].source == "circular"
        assert metrics[name].certifiable is False
    for name, min_n in CERT_MIN_N.items():
        assert metrics[name].support < min_n
        assert metrics[name].certifiable is False
        assert metrics[name].f1_ci95[0] < 0.98


def test_confidence_intervals_are_computed():
    lo, hi = wilson_interval(15, 16)
    assert 0.0 <= lo <= hi <= 1.0
    metrics = run_all()
    for m in metrics:
        assert len(m.precision_ci95) == 2
        assert len(m.recall_ci95) == 2
        assert len(m.f1_ci95) == 2
        assert m.precision_ci95[0] <= m.precision <= m.precision_ci95[1] + 1e-9 or m.true_positives + m.false_positives == 0


def test_reviewer_agreement_is_unmeasured():
    report = agreement_report(load_reviews())
    assert report["n"] == 0
    assert report["cohen_a_b"] is None
    assert "unmeasured" in report["note"].lower()


def test_verification_never_invents_on_empty():
    result = verify_reference()
    assert result.status == "could_not_verify"
    assert result.confidence == 0


def test_kappa_helpers_on_synthetic_labels():
    a = ["strong", "weak", "missing", "strong"]
    b = ["strong", "weak", "missing", "weak"]
    kappa = cohen_kappa(a, b)
    assert kappa is not None
    assert 0.0 < kappa < 1.0
    fleiss = fleiss_kappa([["a", "a", "a"], ["a", "b", "a"]])
    assert fleiss is not None


def test_hallucination_redteam_has_1000_block_cases():
    suite = build_hallucination_suite()
    block = [c for c in suite if not c[2]]
    assert len(block) >= 1000
    rates = hallucination_escape_rate(suite)
    assert rates["n_should_block"] >= 1000
    assert 0.0 <= rates["escape_rate"] <= 1.0


def test_citation_parser_corpus_is_unlabeled_and_large():
    cases = citation_parser_cases()
    assert len(cases) >= 2000
    report = parser_robustness()
    assert report["n"] >= 2000
    assert report["labeled_for_f1"] is False
    assert report["failures"] == 0


def test_live_eval_and_prompt_registry_do_not_invent_accuracy():
    live = live_eval_status()
    assert live["n_run"] == 0
    for row in live["providers"]:
        assert row["accuracy"] is None
    gate = regression_gate(None, None)
    assert gate["allow_deploy"] is False
    registry = registry_report()
    assert registry["gate"]["allow_deploy"] is False


def test_certification_bundle_refuses_98():
    extras = extras_bundle()
    assert extras["reviewer_agreement"]["n"] == 0
    assert extras["verification"]["precision"] is None
    assert extras["live_llm"]["n_run"] == 0
    assert extras["calibration"]["exposed_in_ui"] is False
    assert extras["calibration"]["passes_calibration"] is False
    metrics = run_all()
    from app.services.ai.eval import certification_verdict

    verdict = certification_verdict(metrics, extras)
    assert verdict["claim_98"] is False
    assert verdict["certified"] is False
