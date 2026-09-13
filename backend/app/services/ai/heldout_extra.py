"""Additional independent held-out items. Hand-written, not generated from eval templates."""

from __future__ import annotations

QUESTION_EXTRA: list[tuple[str, set[str]]] = [
    ("Critique the proportionality test as a constraint on emergency powers in UK public law.", {"critique"}),
    ("Explain why prestressed concrete members can fail in shear even when flexural capacity is adequate.", {"explain"}),
    ("Argue that informed consent in paediatric trials cannot rest on parental signature alone.", {"argue"}),
    ("Contrast doctrinal and socio-legal approaches to contract interpretation.", {"contrast"}),
    ("Explore uncertainty in climate attribution for West African drought.", {"explore"}),
    ("Illustrate capability deprivation using one rural health example, then assess policy.", {"illustrate", "assess"}),
    ("Summarise the main claims in Why Nations Fail without adding sources.", {"summarise"}),
    ("Account for persistent informal employment in Ghana after structural adjustment.", {"account for"}),
    ("In medical ethics, evaluate substitute decision-making against best-interests tests.", {"evaluate"}),
    ("For engineering management, assess lifecycle cost of rural electrification in Kenya.", {"assess"}),
    ("In history, examine testimony as evidence in oral histories of decolonisation.", {"examine"}),
    ("In business strategy, compare family-firm succession in two emerging-market cases.", {"compare"}),
    ("In economics, to what extent does exchange-rate pass-through explain consumer inflation?", {"to what extent"}),
    ("In law, justify limiting police stop-and-search using procedural-justice research.", {"justify"}),
    ("In the humanities, discuss canon formation in African philosophy.", {"discuss"}),
    ("In social science, analyse welfare conditionality and stigma.", {"analyse"}),
    ("In science policy, review evidence on vaccine allocation rules.", {"review"}),
    ("Determine whether diagnostic delay in tuberculosis programmes is primarily a laboratory constraint.", {"determine"}),
    ("How far can board independence improve earnings quality without changing incentives?", {"how far"}),
    ("Outline failure modes in industrial control systems, then recommend a mitigation order.", {"outline", "recommend"}),
]

THESIS_EXTRA: list[tuple[str, str, str]] = [
    (
        "Evaluate emergency powers in UK public law.",
        "Emergency statutes should be treated as constitutionally exceptional because they weaken ordinary legislative scrutiny.",
        "strong",
    ),
    (
        "Evaluate emergency powers in UK public law.",
        "This essay is about emergency powers.",
        "weak",
    ),
    (
        "Assess informed consent in paediatric trials.",
        "Parental signature is not a substitute for a child's developing assent; trials should be judged by comprehension, not paperwork.",
        "strong",
    ),
    (
        "Assess informed consent in paediatric trials.",
        "The next section lists definitions used in paediatric research ethics.",
        "missing",
    ),
    (
        "Compare import substitution and export orientation.",
        "Export orientation outperforms import substitution because upgrading, not openness, determines firm capability; otherwise liberalisation widens inequality.",
        "strong",
    ),
    (
        "Discuss social media and political participation.",
        "This paper will discuss some aspects of social media.",
        "weak",
    ),
    (
        "Analyse board independence and earnings quality.",
        "Independence on paper fails when related-party transactions remain unpriced; earnings quality depends on those constraints.",
        "strong",
    ),
    (
        "Examine memory and testimony in oral history.",
        "Testimony is evidence of experience, not a transcript of events; oral history should be read against archive gaps.",
        "strong",
    ),
    (
        "Evaluate the effects of globalization on developing economies.",
        "Background on trade volumes after 1980 is presented first.",
        "missing",
    ),
    (
        "Assess antimicrobial stewardship.",
        "I will write about stewardship and related hospital issues.",
        "weak",
    ),
    (
        "Critique the proportionality test.",
        "This dissertation argues that proportionality is limited unless courts can review evidential adequacy, not merely ends.",
        "strong",
    ),
    (
        "Explore climate attribution.",
        "This article will explore climate attribution without taking a position.",
        "weak",
    ),
]

ARGUMENT_EXTRA: list[tuple[str, bool]] = [
    ("The court should require evidential adequacy because emergency powers otherwise become self-justifying. Therefore proportionality without facts is empty.", True),
    ("Critics argue that rural clinics lack staff; however, user-fee removal still increased visits where drugs remained in stock.", True),
    ("Although flexural capacity was adequate, shear reinforcement was omitted, so the member can fail before the design moment.", True),
    ("There is a literature on emergency powers.", False),
    ("The next chapter lists definitions of informed consent.", False),
    ("Background material on oral history is arranged chronologically.", False),
    ("A list of dates follows the introduction of vaccine allocation.", False),
    ("This shows that independence on boards cannot be reduced to a headcount of outsiders.", True),
    ("Consequently, lifecycle cost must include diesel backup, not only panel prices.", True),
    ("There are several handbooks that mention prestressed concrete.", False),
]

EVIDENCE_EXTRA: list[tuple[str, str]] = [
    ("Inflation reached 12 percent during the episode linked to fuel subsidy removal.", "needs_citation"),
    ("Inflation reached 12 percent during the episode (Stiglitz, 2002).", "supported"),
    ("A study found mixed results for board independence after IFRS adoption.", "needs_citation"),
    ("Research indicates that shear failures clustered in members without stirrups.", "needs_citation"),
    ("Research indicates mixed results (Acemoglu and Robinson, 2012).", "supported"),
    ("Everyone knows that liberalization always proves that poverty disappears.", "potentially_unsupported"),
    ("A thesis should answer the question rather than announce a topic.", "cannot_determine"),
    ("Evaluation of stewardship requires resistance rates, not only policy documents.", "cannot_determine"),
    ("Statistics show rapid change in informal employment.", "needs_citation"),
    ("GDP grew by 7 percent after liberalisation (Rodrik, 2011).", "supported"),
]

CITATION_EXTRA: list[tuple[str, str, int, int]] = [
    ("Sen (1999) argues that development is an expansion of capabilities.", "apa7", 1, 0),
    ("Institutions matter (Acemoglu & Robinson, 2012).", "apa7", 1, 0),
    ("Capability matters (Rodrik 2011).", "harvard", 1, 0),
    ("(Smith 42) offers a page-number citation.", "mla9", 1, 0),
    ("Prior work [1], [2] frames the safety case.", "ieee", 2, 0),
    ("(Rodrik 2011, 44) uses a Chicago author-date locator.", "chicago", 1, 0),
    ("Some people say this is true without a source.", "apa7", 0, 0),
    ("Rodrik (2011) and Rodrik (2011) repeat the same in-text cite.", "apa7", 2, 0),
    ("See also recent commentary without a year or author.", "apa7", 0, 0),
    (
        "Trade rose (Rodrik, 2011).\n\nReferences\nRodrik, D. (2011). The globalization paradox. W. W. Norton.",
        "apa7",
        1,
        1,
    ),
    ("Mkandawire (2001) discusses social policy in a development context.", "apa7", 1, 0),
    ("(Fanon 1789) uses a year outside the 19xx/20xx extractor window.", "harvard", 0, 0),
    ("Incomplete: (Rodrik).", "apa7", 0, 0),
    ("Mixed: Rodrik (2011) and also [3] in the same sentence.", "apa7", 1, 0),
    (
        "Works Cited\nSen, A. Development as Freedom. Anchor, 1999.",
        "mla9",
        0,
        1,
    ),
]
