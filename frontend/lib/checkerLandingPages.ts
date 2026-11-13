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
const handCraftedPages: Record<string, CheckerLandingPage> = {
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
          "Yes. Every feature is free right now, with no monthly check cap. You can start without an account.",
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
  "literature-review-checker": {
    title: "Free Literature Review Checker | AcademicCheck AI",
    description:
      "Check whether your literature review synthesises sources, answers the research question, and cites consistently. Diagnostic feedback, not a grade.",
    heading: "Literature review checker",
    eyebrow: "Before you submit the review",
    intro:
      "A literature review is judged on synthesis, not on how many papers you summarise. Paste the research question and the draft. AcademicCheck looks at whether sources are compared, whether the gap is clear, and whether citations match the reference list.",
    checks: [
      "Whether paragraphs compare sources instead of listing them one by one",
      "Whether the review stays tied to the research question",
      "Citation and reference consistency across a long source list",
    ],
    howItWorks: [
      {
        step: "01",
        title: "Add the question and draft",
        body: "Paste the research question or chapter brief with the review. A review without a question cannot be checked for relevance.",
      },
      {
        step: "02",
        title: "See synthesis gaps",
        body: "The report flags description-heavy sections and ranks what to revise first.",
      },
      {
        step: "03",
        title: "Rewrite the weak paragraphs",
        body: "You keep authorship. The checker does not draft the review for you.",
      },
    ],
    sample: {
      score: 71,
      readiness: "Needs synthesis, not more sources",
      findings: [
        { title: "Source listing", detail: "Three paragraphs summarise one paper each and never compare them." },
        { title: "Research question", detail: "The gap is named in the introduction and then disappears." },
        { title: "References", detail: "Four in-text citations have no matching reference-list entry." },
      ],
    },
    sections: [
      {
        heading: "What markers look for in a literature review",
        paragraphs: [
          "A strong review groups sources by theme or debate. It says how studies agree, where they conflict, and what is still missing. A weak review reads like annotated bibliography paragraphs placed in a row.",
          "Before you add another paper, check whether the ones you already have are in conversation. AcademicCheck is useful at that moment: it shows whether the draft still answers the question you set.",
        ],
      },
      {
        heading: "A revision order that saves time",
        paragraphs: [
          "First, write one sentence that states the gap. Then make every theme paragraph end by relating back to that sentence. Only after the argument is stable should you tidy APA, Harvard, or the style your department requires.",
          "Run the checker once on the full draft, revise the top priorities, and run it again. The second pass is where orphaned citations usually show up.",
        ],
      },
    ],
    faqs: [
      {
        question: "Is the literature review checker free?",
        answer: "Yes. Full analysis, citations, PDF export, and draft comparison are free right now, with no monthly cap.",
      },
      {
        question: "Will it write my literature review?",
        answer: "No. It diagnoses the draft you wrote. You revise the synthesis yourself.",
      },
      {
        question: "Does a high score mean my supervisor will pass it?",
        answer: "No. The score is a diagnostic, not an official mark.",
      },
    ],
    related: [
      { href: "/resources/how-to-write-a-literature-review", label: "How to write a literature review" },
      { href: "/citation-checker", label: "Citation checker" },
      { href: "/thesis-checker", label: "Thesis checker" },
      { href: "/check", label: "Check a draft" },
    ],
    cta: "Check my literature review",
  },
  "reflective-essay-checker": {
    title: "Free Reflective Essay Checker | AcademicCheck AI",
    description:
      "Check a reflective essay for a real critical incident, analysis, and a link back to the brief. Not a grade and not a rewrite.",
    heading: "Reflective essay checker",
    eyebrow: "Reflection, not a diary",
    intro:
      "Reflective essays lose marks when they stay at story level. Paste the brief and the draft. AcademicCheck checks whether you describe an experience, analyse it, and connect it to the module outcome.",
    checks: [
      "Whether the draft goes beyond narration into analysis",
      "Whether the reflection answers the set brief",
      "Whether the conclusion states what will change in practice",
    ],
    howItWorks: [
      {
        step: "01",
        title: "Paste the brief",
        body: "Include the learning outcome or question. Reflection without a target is hard to assess.",
      },
      {
        step: "02",
        title: "Find the descriptive stretch",
        body: "The report highlights sections that retell events without explaining why they matter.",
      },
      {
        step: "03",
        title: "Add the analysis yourself",
        body: "You write the judgement. The tool does not invent a model or a quote for you.",
      },
    ],
    sample: {
      score: 68,
      readiness: "Story is clear; analysis is thin",
      findings: [
        { title: "Description", detail: "The first half retells the shift and never names what was learned." },
        { title: "Theory", detail: "A model is mentioned once and not used to interpret the incident." },
        { title: "Future practice", detail: "The ending summarises the story instead of stating a change." },
      ],
    },
    sections: [
      {
        heading: "Description, analysis, and future action",
        paragraphs: [
          "A workable reflective paragraph has three moves: what happened, why it mattered, and what you will do differently. Markers can see when the middle move is missing, even if the prose is fluent.",
          "If your module names a model, use it to interpret the incident. Naming the model in the introduction and never returning to it does not count as application.",
        ],
      },
    ],
    faqs: [
      {
        question: "Is this free?",
        answer: "Yes. You can check a reflective draft now, with no account required for the first session.",
      },
      {
        question: "Can it turn my notes into a reflective essay?",
        answer: "No. It reviews a draft you have written. It does not ghostwrite the essay.",
      },
    ],
    related: [
      { href: "/resources/how-to-write-a-reflective-essay", label: "How to write a reflective essay" },
      { href: "/assignment-checker", label: "Assignment checker" },
      { href: "/check", label: "Check a draft" },
    ],
    cta: "Check my reflection",
  },
  "lab-report-checker": {
    title: "Free Lab Report Checker | AcademicCheck AI",
    description:
      "Check a lab report for aim, method, results, and a discussion that actually interprets the data. Diagnostic only.",
    heading: "Lab report checker",
    eyebrow: "Results need interpretation",
    intro:
      "Lab reports lose marks when the discussion repeats the results. Paste the aim and the report. AcademicCheck checks whether the method is followable, whether results are reported before interpretation, and whether the discussion answers the aim.",
    checks: [
      "Whether the discussion interprets results instead of repeating them",
      "Whether the report stays aligned with the stated aim",
      "Whether citations in the introduction and discussion are consistent",
    ],
    howItWorks: [
      {
        step: "01",
        title: "Include the aim",
        body: "Paste the practical brief or aim with the report so the discussion can be checked against it.",
      },
      {
        step: "02",
        title: "See the weak section",
        body: "The report ranks whether method, results, or discussion needs work first.",
      },
      {
        step: "03",
        title: "Revise that section",
        body: "You rewrite the science. The checker does not invent data or references.",
      },
    ],
    sample: {
      score: 73,
      readiness: "Results are fine; discussion is thin",
      findings: [
        { title: "Aim", detail: "The aim asks about temperature, but the discussion explains equipment instead." },
        { title: "Results", detail: "Figures are described again in the discussion without a claim." },
        { title: "Sources", detail: "Two comparison studies are cited and missing from the reference list." },
      ],
    },
    sections: [
      {
        heading: "The section markers read twice",
        paragraphs: [
          "Method and raw results are necessary. The mark often sits in the discussion: what the result means, how it compares with expected theory, and what limited the experiment. If that section only restates numbers, the report is unfinished.",
          "Do not ask a tool to fabricate results. AcademicCheck reviews the report you wrote from the experiment you did.",
        ],
      },
    ],
    faqs: [
      {
        question: "Will it calculate my results?",
        answer: "No. It reviews how the report presents and interprets results you already have.",
      },
      {
        question: "Is the lab report check free?",
        answer: "Yes. There is no monthly check cap during this free period.",
      },
    ],
    related: [
      { href: "/resources/how-to-write-a-lab-report", label: "How to write a lab report" },
      { href: "/citation-checker", label: "Citation checker" },
      { href: "/check", label: "Check a draft" },
    ],
    cta: "Check my lab report",
  },
  "case-study-checker": {
    title: "Free Case Study Checker | AcademicCheck AI",
    description:
      "Check whether a case study applies theory to the case, answers the question, and cites the case evidence. Not a grade.",
    heading: "Case study checker",
    eyebrow: "Theory has to meet the case",
    intro:
      "Case studies fail when theory and the case never meet. Paste the question and the draft. AcademicCheck checks whether you use the case as evidence, apply a framework, and reach a recommendation the question asked for.",
    checks: [
      "Whether theory is applied to case facts, not explained in the abstract",
      "Whether the recommendation answers the question",
      "Whether case evidence and external sources are cited consistently",
    ],
    howItWorks: [
      {
        step: "01",
        title: "Paste the case question",
        body: "The question decides whether you should recommend, evaluate, or compare options.",
      },
      {
        step: "02",
        title: "Find unused theory",
        body: "The diagnosis shows frameworks that are defined and then abandoned.",
      },
      {
        step: "03",
        title: "Tie each claim to the case",
        body: "You write the application. The tool does not invent case facts.",
      },
    ],
    sample: {
      score: 70,
      readiness: "Framework is named; case is thin",
      findings: [
        { title: "Application", detail: "SWOT is defined for a page and never used on the company." },
        { title: "Question", detail: "The brief asks for a recommendation. The ending only summarises theory." },
        { title: "Evidence", detail: "Case figures are mentioned with no source line." },
      ],
    },
    sections: [
      {
        heading: "Apply, then recommend",
        paragraphs: [
          "A case paragraph should name a concept, point at a fact from the case, and say what that fact implies. A recommendation should follow from those implications and match the command word in the question.",
          "If you cannot point to a sentence in the case, the claim is unsupported. Fix that before you polish the prose.",
        ],
      },
    ],
    faqs: [
      {
        question: "Can it solve the case for me?",
        answer: "No. It reviews your analysis. You decide the recommendation.",
      },
      {
        question: "Is it free?",
        answer: "Yes. Case-study checks are included, with no monthly cap right now.",
      },
    ],
    related: [
      { href: "/resources/how-to-answer-a-case-study", label: "How to answer a case study" },
      { href: "/assignment-checker", label: "Assignment checker" },
      { href: "/check", label: "Check a draft" },
    ],
    cta: "Check my case study",
  },
};

type MoneySpec = {
  slug: string;
  label: string;
  focus: string;
  audience?: string;
};

const MONEY_SPECS: MoneySpec[] = [
  { slug: "ai-essay-checker", label: "AI essay checker", focus: "whether the draft answers the brief—not generic AI writing polish alone" },
  { slug: "essay-checker", label: "Essay checker", focus: "question fit, thesis strength, argument, evidence, and citation consistency" },
  { slug: "academic-writing-checker", label: "Academic writing checker", focus: "clarity, structure, and whether claims stay academic rather than conversational" },
  { slug: "ai-assignment-checker", label: "AI assignment checker", focus: "assignment-question relevance first, then thesis, evidence, and citations" },
  { slug: "research-paper-checker", label: "Research paper checker", focus: "argument coherence, evidence integration, and reference consistency for longer papers" },
  { slug: "dissertation-checker", label: "Dissertation checker", focus: "chapter-level argument, research question alignment, and citation hygiene on long drafts" },
  { slug: "essay-grammar-checker", label: "Essay grammar checker", focus: "clarity issues that block marks—while still checking whether you answered the question" },
  { slug: "academic-grammar-checker", label: "Academic grammar checker", focus: "formal clarity and sentence control without turning the draft into empty polish" },
  { slug: "essay-structure-checker", label: "Essay structure checker", focus: "introduction–body–conclusion flow and whether each section serves the question" },
  { slug: "thesis-statement-checker", label: "Thesis statement checker", focus: "whether the thesis is contestable and answers the command word" },
  { slug: "argument-checker", label: "Argument checker", focus: "claim–reason–evidence links and missing counterargument" },
  { slug: "paragraph-checker", label: "Paragraph checker", focus: "topic sentences, relevance to the thesis, and evidence that actually supports each claim" },
  { slug: "apa-citation-checker", label: "APA citation checker", focus: "APA 7 in-text and reference-list consistency before you submit" },
  { slug: "mla-citation-checker", label: "MLA citation checker", focus: "MLA 9 works-cited and in-text consistency" },
  { slug: "harvard-citation-checker", label: "Harvard citation checker", focus: "Harvard author–date consistency across body and reference list" },
  { slug: "grammar-checker", label: "Grammar checker for students", focus: "readable academic prose—paired with brief-fit diagnostics, not spellcheck alone" },
  { slug: "ai-writing-checker", label: "AI writing checker", focus: "diagnostic feedback on your draft; not a misconduct verdict or AI detector score" },
  { slug: "essay-checker-ghana", label: "Essay checker for Ghana", focus: "assignment-question fit for Ghanaian university essays and coursework", audience: "students in Ghana" },
  { slug: "assignment-checker-ghana", label: "Assignment checker for Ghana", focus: "whether coursework answers the set question before submission", audience: "students in Ghana" },
  { slug: "essay-checker-nigeria", label: "Essay checker for Nigeria", focus: "question fit, argument, and citations for Nigerian university essays", audience: "students in Nigeria" },
  { slug: "assignment-checker-nigeria", label: "Assignment checker for Nigeria", focus: "assignment relevance and fix-first priorities for Nigerian coursework", audience: "students in Nigeria" },
  { slug: "essay-checker-kenya", label: "Essay checker for Kenya", focus: "brief-fit diagnostics for Kenyan university essays and assignments", audience: "students in Kenya" },
];

function buildMoneyPage(spec: MoneySpec): CheckerLandingPage {
  const who = spec.audience ? ` Built for ${spec.audience}.` : "";
  return {
    title: `${spec.label} | Free diagnostic before you submit | AcademicCheck AI`,
    description: `Free ${spec.label.toLowerCase()}. AcademicCheck AI checks ${spec.focus}.${who} Diagnostic feedback—not an official grade.`,
    heading: spec.label,
    eyebrow: "Buyer-intent tool page",
    intro: `Paste your draft with the assignment question. AcademicCheck AI checks ${spec.focus}, then ranks what to fix first.${who} Feedback is diagnostic, not an official grade.`,
    checks: [
      "Whether the draft responds to the assignment question and command words",
      "Thesis, argument, evidence, and structure that markers usually reward",
      "Citation and reference consistency for common university styles",
    ],
    howItWorks: [
      {
        step: "01",
        title: "Add question + draft",
        body: "Paste text or upload DOCX/PDF. Include the assignment question so relevance can be checked properly.",
      },
      {
        step: "02",
        title: "Get a diagnosis",
        body: "Receive an Academic Health Score with Fix-First priorities—not vague tips alone.",
      },
      {
        step: "03",
        title: "Revise your own work",
        body: "Use the report to improve writing you authored. AcademicCheck does not ghostwrite submissions.",
      },
    ],
    sample: {
      score: 74,
      readiness: "Needs focused revision",
      findings: [
        {
          title: "Question alignment",
          detail: "The draft covers the topic but under-addresses the command word in the brief.",
        },
        {
          title: "Evidence depth",
          detail: "Key claims need closer source integration before the conclusion can persuade.",
        },
        {
          title: "Citation consistency",
          detail: "A few in-text citations and reference-list entries need a tidy pass.",
        },
      ],
    },
    sections: [
      {
        heading: `What a strong ${spec.label.toLowerCase()} actually checks`,
        paragraphs: [
          `Most tools polish sentences. Markers mark whether you answered the question. A useful ${spec.label.toLowerCase()} therefore starts with the brief: Does the work obey the command word? Does the thesis make a contestable claim?`,
          `AcademicCheck AI is built around that order: question fit, thesis, argument, evidence, structure, writing, and citations—so limited revision time goes where marks are most often won or lost.`,
        ],
      },
      {
        heading: "How this differs from Grammarly or a generic chatbot",
        paragraphs: [
          "Grammar tools improve wording. Chatbots can imitate feedback in one session. AcademicCheck persists a diagnostic against your assignment question, ranks fixes, and keeps integrity boundaries: no ghostwriting, no invented references.",
          "Use the report to revise your own work. Always follow your institution’s academic-integrity policies.",
        ],
      },
      {
        heading: "A practical pre-submission workflow",
        paragraphs: [
          "Freeze the argument before obsessing over commas. Run the check with the full question and draft. Fix the top priorities, then re-check once so edits did not create new gaps.",
          "Scores are AI-assisted diagnostic indicators—not a prediction of your lecturer’s grade.",
        ],
      },
    ],
    faqs: [
      {
        question: `Is this ${spec.label.toLowerCase()} free?`,
        answer: "Yes. Every feature is free right now, including full analysis, coach, citations, PDF export, and draft comparison. There is no monthly check cap.",
      },
      {
        question: "Does it write my essay for me?",
        answer: "No. It diagnoses your draft. You revise. Ghostwritten submissions are an integrity failure.",
      },
      {
        question: "Is the score an official grade?",
        answer: "No. It is diagnostic feedback to guide revision before you submit.",
      },
      {
        question: "Do I need the assignment question?",
        answer: "Yes for the best result. Without the brief, tools can only polish prose—not check whether you answered the set question.",
      },
    ],
    related: [
      { href: "/assignment-checker", label: "Assignment checker" },
      { href: "/thesis-checker", label: "Thesis checker" },
      { href: "/citation-checker", label: "Citation checker" },
      { href: "/sample-report", label: "Sample diagnostic report" },
    ],
    cta: "Check my draft",
  };
}

const generatedPages = Object.fromEntries(MONEY_SPECS.map((spec) => [spec.slug, buildMoneyPage(spec)]));

/** All money-page fallbacks: hand-crafted hubs + generated landings for sitemap coverage. */
export const checkerLandingPages: Record<string, CheckerLandingPage> = {
  ...handCraftedPages,
  ...generatedPages,
};

