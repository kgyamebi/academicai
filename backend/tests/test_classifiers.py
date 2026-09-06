from app.services.analysis.classifiers import classify_thesis, has_reasoned_argument, needs_citation, rubric_covered


def test_classify_thesis_three_classes():
    q = "Evaluate the effects of globalization on developing economies."
    assert classify_thesis(
        "This essay argues that industrial policy, not openness alone, determines development outcomes.",
        q,
    ) == "strong"
    assert classify_thesis("This essay is about globalization and developing economies.", q) == "weak"
    assert classify_thesis("Trade has increased in recent decades across several regions.", q) == "missing"
    assert classify_thesis("", q) == "missing"


def test_reasoned_argument_requires_claim_marker():
    assert has_reasoned_argument("Therefore openness alone does not determine outcomes.")
    assert not has_reasoned_argument("There is a literature on trade policy.")


def test_needs_citation_ignores_already_cited_claims():
    assert needs_citation("GDP grew by 7 percent after liberalisation.")
    assert not needs_citation("GDP grew by 7 percent after liberalisation (Rodrik, 2011).")
    assert not needs_citation("A thesis should be contestable rather than a topic label.")


def test_rubric_covered_maps_evaluation_to_relevance():
    criteria = [{"name": "Evaluation"}, {"name": "Thesis"}, {"name": "Unknown criterion"}]
    covered = rubric_covered(criteria, {"relevance": 70, "thesis": 80, "academic_writing": 40})
    assert "Evaluation" in covered
    assert "Thesis" in covered
    assert "Unknown criterion" not in covered
