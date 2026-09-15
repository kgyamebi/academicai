export type CheckerLandingPage = {
  title: string;
  description: string;
  heading: string;
  eyebrow: string;
  intro: string;
  checks: string[];
  howItWorks: Array<{ step: string; title: string; body: string }>;
  sample: {
    score: number;
    readiness: string;
    findings: Array<{ title: string; detail: string }>;
  };
  sections: Array<{ heading: string; paragraphs: string[] }>;
  faqs: Array<{ question: string; answer: string }>;
  related: Array<{ href: string; label: string }>;
  cta: string;
};

/**
 * Built-in money-page fallbacks for footer/sitemap URLs.
 * Used when production has no matching seo_pages DB row.
 * Database-managed SEO content still takes precedence when present.
 */
export const checkerLandingPages: Record<string, CheckerLandingPage> = {
  "assignment-checker": {
    title: "Free Assignment Checker | Review Before You Submit | AcademicCheck AI",
    description:
      "Free assignment checker for university students. See whether your draft answers the question, supports its argument, and cites sources consistently—before submission.",
    heading: "Free assignment checker",
    eyebrow: "Buyer-intent tool page",
    intro:
      "Paste your draft and the assignment question. AcademicCheck AI diagnoses relevance, thesis, argument, evidence, structure, writing clarity, and citation consistency—then shows what to fix first. Feedback is diagnostic, not an official grade.",
    checks: [
      "Whether the draft responds to the assignment question and command words (evaluate, discuss, analyse)",
      "Thesis strength, claim–evidence links, and paragraph relevance",
      "Structure, academic clarity, and citation/reference consistency",
    ],
    howItWorks: [
      {
        step: "01",
        title: "Add your draft",
        body: "Paste text or upload DOCX/PDF. Include the assignment question so relevance can be checked properly.",
      },
      {
        step: "02",
        title: "Get a diagnosis",
        body: "Receive an Academic Health Score with Fix-First priorities—not vague grammar tips alone.",
      },
      {
        step: "03",
        title: "Revise your own work",
        body: "Use the report to improve your writing. AcademicCheck does not ghostwrite submissions for you.",
      },
    ],
    sample: {
      score: 78,
      readiness: "Needs focused revision",
      findings: [
        {
          title: "Question alignment",
          detail: "Introduction restates the topic but under-addresses the evaluate command.",
        },
        {
          title: "Evidence depth",
          detail: "Two key claims rely on description rather than analysis of sources.",
        },
        {
          title: "Citation consistency",
          detail: "In-text years missing for two references; style drift between APA and Harvard patterns.",
        },
      ],
    },
    sections: [
      {
        heading: "What a strong assignment check actually looks for",
        paragraphs: [
          "Most students revise sentences first. Markers usually mark argument quality first. An assignment checker should therefore start with the brief: Does the work answer the question that was set? Does it obey the command word? Does the thesis make a contestable claim rather than announcing a topic?",
          "From there, useful feedback inspects whether each paragraph advances the argument, whether evidence is explained rather than merely dropped in, and whether the conclusion returns a judgement rather than a summary list. Grammar still matters, but polishing prose before fixing relevance often wastes the revision window.",
          "AcademicCheck AI is built around that order of operations. It surfaces question fit, thesis, argument, evidence, structure, writing, and citations so you can spend limited time where marks are most often won or lost.",
        ],
      },
      {
        heading: "How to use an assignment checker before submission",
        paragraphs: [
          "Run the check once you have a complete draft—not only an outline. Incomplete sections create false alarms. Paste the full brief or question so the model can compare your claims against what was asked.",
          "Read Fix-First items in order. If relevance or thesis is weak, fix those before chasing comma rules. After a focused revision pass, re-check to confirm the diagnosis moved. Treat the score as a readiness signal for your own editing, never as a predicted grade.",
          "Keep your institution’s integrity policy in view. Using feedback to improve your reasoning is normal academic practice. Asking a tool to invent sources, fabricate analysis, or write the assignment for you is not.",
        ],
      },
      {
        heading: "Assignment checker vs grammar checker",
        paragraphs: [
          "A grammar checker improves local correctness. An assignment checker interrogates academic fitness for purpose. You can have fluent sentences that still fail because they never answer the question, never take a position, or never analyse evidence.",
          "If you only run a spelling pass, you may submit a polished draft that still misses the mark scheme. Pair clarity tools with a relevance-and-argument review—especially for essays, reports, and discursive coursework where criteria emphasise critical engagement.",
        ],
      },
      {
        heading: "Who this free assignment checker is for",
        paragraphs: [
          "Undergraduate and postgraduate students who want a pre-submission diagnosis. It is also useful for returning adults and international students who want clearer signals on structure and academic conventions without outsourcing authorship.",
          "Lecturers and tutors sometimes share the sample report with students as a model of diagnostic feedback. The product remains student-facing: it helps people revise their own work, not generate ghostwritten submissions.",
        ],
      },
    ],
    faqs: [
      {
        question: "Is the assignment checker free?",
        answer:
          "You can start with a free first check without buying a plan. Create an account if you want to save work and return to reports later.",
      },
      {
        question: "Does the assignment checker give a grade?",
        answer:
          "No. It provides AI-assisted diagnostic feedback and a readiness-style score. It is not an official mark or lecturer assessment.",
      },
      {
        question: "Will it write my assignment for me?",
        answer:
          "No. AcademicCheck highlights weaknesses and priorities so you can revise your own work. It is not a ghostwriting service.",
      },
      {
        question: "What files can I check?",
        answer:
          "Paste text directly or upload common coursework formats such as DOCX and PDF, then include the assignment question for best relevance checks.",
      },
    ],
    related: [
      { href: "/thesis-checker", label: "Thesis checker" },
      { href: "/citation-checker", label: "Citation checker" },
      { href: "/sample-report", label: "Sample diagnostic report" },
      { href: "/resources", label: "Writing resources hub" },
    ],
    cta: "Check my assignment free",
  },

  "thesis-checker": {
    title: "Thesis Statement Checker | Test If Your Claim Is Arguable | AcademicCheck AI",
    description:
      "Free thesis statement checker for essays and assignments. Test whether your thesis is specific, arguable, aligned to the question, and supported by your draft.",
    heading: "Thesis statement checker",
    eyebrow: "Thesis & claim diagnostics",
    intro:
      "A thesis is a contestable answer to the question—not a topic label. Use this checker to test specificity, arguability, question alignment, and whether your body paragraphs actually support the claim you announced.",
    checks: [
      "Whether the central claim is specific and arguable rather than descriptive",
      "Alignment between thesis, assignment question, and introduction framing",
      "Whether evidence and paragraph topic sentences support the announced claim",
    ],
    howItWorks: [
      {
        step: "01",
        title: "Paste draft + question",
        body: "Include your introduction and enough body paragraphs for the checker to see whether the claim is carried through.",
      },
      {
        step: "02",
        title: "Inspect the claim",
        body: "See signals on vagueness, topic-only statements, missing stance, and drift between thesis and body.",
      },
      {
        step: "03",
        title: "Rewrite the thesis yourself",
        body: "Tighten the claim, then adjust topic sentences so each paragraph defends it. Re-check after revision.",
      },
    ],
    sample: {
      score: 71,
      readiness: "Thesis needs sharpening",
      findings: [
        {
          title: "Claim specificity",
          detail: "Current thesis names the topic but does not state a contestable position.",
        },
        {
          title: "Question fit",
          detail: "Brief asks for evaluation; thesis stays descriptive (“this essay discusses…”).",
        },
        {
          title: "Body support",
          detail: "Paragraph three introduces a new criterion never previewed in the thesis.",
        },
      ],
    },
    sections: [
      {
        heading: "What makes a university thesis statement strong",
        paragraphs: [
          "A strong thesis answers the question with a focused, arguable claim that the essay can support. “Social media affects students” is a topic. “Mandatory phone bans in exam halls improve integrity more than honour codes alone because detection risk changes behaviour” is closer to a thesis: it takes a position and implies criteria.",
          "Markers look for contestability. If no reasonable reader could disagree, you probably wrote a summary, not an argument. Markers also look for scope: a claim wide enough to matter, narrow enough to defend in the word limit.",
          "Finally, the thesis should preview the logic of the essay without becoming a laundry list. Readers should know what judgement you will defend and roughly on what grounds.",
        ],
      },
      {
        heading: "Common thesis failures this checker helps you catch",
        paragraphs: [
          "Announcement theses (“This paper will discuss…”) signal organisation, not argument. Descriptive theses restate facts without judgement. Split theses smuggle two unrelated claims into one sentence and then defend only one.",
          "Another frequent failure is thesis drift: a clear claim in the introduction, then body paragraphs that chase interesting side points. A thesis checker that only rewrites the sentence in isolation is less useful than one that also asks whether the draft supports the claim.",
          "Use the report to decide whether you need a sharper sentence, a narrower scope, or a restructuring of topic sentences so the body matches the promise of the introduction.",
        ],
      },
      {
        heading: "How to revise a weak thesis without starting over",
        paragraphs: [
          "Return to the exact question and underline the command word. Convert your current thesis into a one-sentence answer. Ask: What would someone who disagrees say? If you cannot invent a fair objection, the claim is probably too bland.",
          "Next, list the two or three reasons your body already develops. Fold those reasons into a more precise claim, then rewrite topic sentences so each paragraph clearly advances one reason. Only after that pass should you polish wording.",
          "Re-run the thesis checker after structural edits. Sentence-level elegance cannot rescue a claim the evidence never supports.",
        ],
      },
      {
        heading: "Thesis checker and academic integrity",
        paragraphs: [
          "Using a thesis checker to pressure-test your thinking is similar to asking a peer: “Is my claim clear?” It becomes an integrity problem if you outsource the argument itself, invent evidence, or submit AI-written prose as your own where policy forbids it.",
          "AcademicCheck is designed as a diagnostic aid. It does not replace your lecturer’s criteria, and it does not certify originality. Always follow your department’s rules on AI-assisted study tools.",
        ],
      },
    ],
    faqs: [
      {
        question: "What makes a thesis statement strong?",
        answer:
          "It answers the question with a focused, arguable claim that the essay can support with reasoning and evidence—not a topic announcement.",
      },
      {
        question: "Can a thesis checker replace lecturer feedback?",
        answer:
          "No. Use it as a revision aid alongside your course guidance, rubric, and marking criteria.",
      },
      {
        question: "Should I check only the thesis sentence?",
        answer:
          "Checking the sentence helps, but including surrounding paragraphs is better because support and drift matter as much as wording.",
      },
      {
        question: "Does this work for reports as well as essays?",
        answer:
          "Yes, whenever your brief expects a central claim, recommendation, or evaluative position rather than pure description.",
      },
    ],
    related: [
      { href: "/assignment-checker", label: "Assignment checker" },
      { href: "/blog/how-to-write-a-strong-thesis-statement", label: "How to write a strong thesis" },
      { href: "/sample-report", label: "Sample diagnostic report" },
      { href: "/resources", label: "Writing resources hub" },
    ],
    cta: "Check my thesis",
  },

  "citation-checker": {
    title: "Citation Checker | APA, MLA, Harvard Consistency Review | AcademicCheck AI",
    description:
      "Free citation checker for essays and assignments. Review in-text citations, reference lists, and consistency across APA, MLA, Harvard, Chicago, and IEEE before you submit.",
    heading: "Citation checker",
    eyebrow: "References & in-text consistency",
    intro:
      "Citation errors are easy to miss under deadline pressure. This checker helps you spot mismatches between in-text citations and the reference list, style drift, and incomplete reference details—so you can verify sources yourself before submission.",
    checks: [
      "Consistency between in-text citations and the reference / works-cited list",
      "Citation-style patterns for APA, MLA, Harvard, Chicago, and IEEE",
      "Missing years, broken author–year pairs, and incomplete reference fields that need manual verification",
    ],
    howItWorks: [
      {
        step: "01",
        title: "Upload the full draft",
        body: "Include both the body and the reference list so mismatches can be detected.",
      },
      {
        step: "02",
        title: "Review flagged gaps",
        body: "See likely inconsistencies, missing details, and style drift—not a promise that every source is real.",
      },
      {
        step: "03",
        title: "Verify sources yourself",
        body: "Fix formatting and confirm every citation points to a source you actually read and can defend.",
      },
    ],
    sample: {
      score: 82,
      readiness: "Citation tidy-up recommended",
      findings: [
        {
          title: "In-text ↔ reference match",
          detail: "Two in-text citations have no corresponding reference-list entry.",
        },
        {
          title: "Style consistency",
          detail: "Body mixes author–date and footnote-like patterns mid-essay.",
        },
        {
          title: "Reference completeness",
          detail: "Three web sources lack retrieval details required by the chosen style.",
        },
      ],
    },
    sections: [
      {
        heading: "Why citation checking matters more than last-minute formatting",
        paragraphs: [
          "Markers often treat citation quality as a proxy for academic care. Missing references, invented details, and mixed styles undermine trust even when the argument is otherwise solid. A citation checker is most valuable when it catches structural problems: citations without references, references never cited, and inconsistent patterns across the document.",
          "Formatting perfection still requires your style guide. Automated tools approximate patterns; departments differ on hanging indents, DOI display, and secondary citations. Use the checker to find issues, then confirm against APA 7, MLA 9, Harvard, Chicago, or IEEE as required.",
        ],
      },
      {
        heading: "What this citation checker can and cannot do",
        paragraphs: [
          "It can highlight inconsistencies and incomplete-looking entries. It can help you notice when an in-text citation appears to lack a matching reference. It cannot prove a source exists, validate paywalled metadata in every case, or replace your obligation to read and understand the works you cite.",
          "Never treat an automated pass as permission to keep a reference you have not verified. Fabricated or unverified citations are an integrity failure whether a tool flagged them or not.",
        ],
      },
      {
        heading: "A practical pre-submission citation workflow",
        paragraphs: [
          "Freeze your reference list only after the argument is stable—late claim changes often orphan citations. Then run the citation checker on the full document. Resolve mismatches first, then normalise style, then proofread punctuation in the list.",
          "For every flagged item, open the original source or your notes and confirm author, year, title, and locator. If you cannot verify it, remove it and adjust the sentence. Re-check once after edits so fixes did not introduce new orphans.",
        ],
      },
      {
        heading: "APA, MLA, Harvard, and mixed-style drafts",
        paragraphs: [
          "Students often learn one style in secondary school and another at university, then accidentally mix them. Author–date years appearing beside numbered IEEE-like brackets is a classic symptom. Pick the style your module requires and apply it end-to-end.",
          "If your handbook is unclear, ask the module convenor. A citation checker can show inconsistency; only your institution can define the required variant of Harvard or the local reference format.",
        ],
      },
    ],
    faqs: [
      {
        question: "Which citation styles can I review?",
        answer:
          "AcademicCheck AI supports feedback patterns for common styles including APA, MLA, Harvard, Chicago, and IEEE.",
      },
      {
        question: "Does a citation check prove that a source is real?",
        answer:
          "No. Automated checks can miss legitimate sources or flag incomplete data. Always verify references yourself.",
      },
      {
        question: "Can it generate my reference list for me?",
        answer:
          "It is not a substitute for reading sources or for fabricating citations. Use it to review consistency in work you authored and sourced yourself.",
      },
      {
        question: "Should I run the citation checker before or after editing?",
        answer:
          "After the argument is mostly stable, then once more after reference edits—so late changes do not leave orphan citations.",
      },
    ],
    related: [
      { href: "/assignment-checker", label: "Assignment checker" },
      { href: "/resources/apa-7-citation-guide", label: "APA 7 citation guide" },
      { href: "/blog/citation-styles-compared", label: "APA vs MLA vs Harvard" },
      { href: "/sample-report", label: "Sample diagnostic report" },
    ],
    cta: "Check my citations",
  },
};
