from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select

from app.core.logging import get_logger
from app.config import get_settings
from app.core.security import hash_password, verify_password
from app.core.time import utcnow
from app.db.session import SessionLocal
from app.models.admin import FeatureFlag
from app.models.billing import Plan
from app.models.content import FAQ, BlogPost, SeoPage
from app.models.user import Role, User
from app.services.entitlements import DEFAULT_FEATURES

log = get_logger("seed")

PLANS = [
    {
        "slug": "free",
        "name": "Free",
        "description": "Try the checker on a short draft. Basic grammar, structure, and question analysis.",
        "price_usd_cents": 0,
        "checks_per_month": 2,
        "max_words": 2000,
        "features": DEFAULT_FEATURES["free"],
        "sort_order": 0,
    },
    {
        "slug": "student",
        "name": "Student",
        "description": "Full assignment analysis, thesis, argument, evidence, and citation checking.",
        "price_usd_cents": 199,
        "checks_per_month": 20,
        "max_words": 10000,
        "features": DEFAULT_FEATURES["student"],
        "sort_order": 1,
    },
    {
        "slug": "pro",
        "name": "Pro Student",
        "description": "Rubric analysis, version comparison, Academic Coach, PDF reports, and AI-writing indicators.",
        "price_usd_cents": 399,
        "checks_per_month": 60,
        "max_words": 25000,
        "features": DEFAULT_FEATURES["pro"],
        "sort_order": 2,
    },
    {
        "slug": "power",
        "name": "Power",
        "description": "Large documents, more checks, priority processing, and extended history.",
        "price_usd_cents": 799,
        "checks_per_month": 200,
        "max_words": 50000,
        "features": DEFAULT_FEATURES["power"],
        "sort_order": 3,
    },
    {
        "slug": "institution",
        "name": "Institution",
        "description": "Custom pricing for universities, writing centres, and tutoring organisations.",
        "price_usd_cents": 0,
        "checks_per_month": 5000,
        "max_words": 80000,
        "features": {**DEFAULT_FEATURES["power"], "sso": True, "admin": True},
        "is_public": True,
        "sort_order": 4,
    },
]


def seed_if_needed() -> None:
    db = SessionLocal()
    try:
        if not db.scalar(select(Role).where(Role.name == "student")):
            for name in ("guest", "student", "tutor", "admin", "institution"):
                db.add(Role(name=name, description=name))
            db.flush()
            for item in PLANS:
                db.add(Plan(**item))
            _seed_content(db)
            _bootstrap_admin(db)
            db.commit()
            log.info("database_seeded")
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        log.error("seed_failed", error=str(exc))
    finally:
        db.close()
    disable_insecure_default_admin()


def disable_insecure_default_admin() -> None:
    """Disable the published audit credential if it is still present."""
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == "admin@academiccheck.ai"))
        if user and user.password_hash and verify_password("ChangeMeAdmin123!", user.password_hash):
            user.is_active = False
            user.is_suspended = True
            user.password_hash = None
            db.commit()
            log.warning("insecure_default_admin_disabled")
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        log.error("admin_disable_failed", error=str(exc))
    finally:
        db.close()


def _bootstrap_admin(db) -> None:
    settings = get_settings()
    email = (settings.admin_bootstrap_email or "").strip().lower()
    password = settings.admin_bootstrap_password or ""
    if not email or not password:
        return
    if len(password) < 16 or password == "ChangeMeAdmin123!":
        log.error("admin_bootstrap_rejected_weak_password")
        return
    admin_role = db.scalar(select(Role).where(Role.name == "admin"))
    existing = db.scalar(select(User).where(User.email == email))
    if existing:
        return
    db.add(
        User(
            email=email,
            password_hash=hash_password(password),
            full_name="AcademicCheck Admin",
            role_id=admin_role.id if admin_role else None,
            email_verified_at=utcnow(),
        )
    )


def _seed_content(db) -> None:
    for key, desc in (
        ("guest_checker", "Allow unauthenticated guest analysis"),
        ("academic_coach", "Academic Coach chat"),
        ("ai_indicator", "Optional AI-writing indicator"),
        ("share_reports", "Shareable report links"),
        ("billing", "Paid plans and credits"),
    ):
        db.add(FeatureFlag(key=key, enabled=True, description=desc))

    seo = [
        ("ai-essay-checker", "AI Essay Checker", "Check structure, thesis, argument, evidence and citations before you submit."),
        ("assignment-checker", "Assignment Checker", "Analyse an assignment against its question, rubric and academic level."),
        ("essay-checker", "Essay Checker", "Find the weaknesses in your essay before your lecturer does."),
        ("academic-writing-checker", "Academic Writing Checker", "Improve clarity, formality and precision without fake complexity."),
        ("ai-assignment-checker", "AI Assignment Checker", "AI-assisted feedback on relevance, argument and academic writing."),
        ("research-paper-checker", "Research Paper Checker", "Check argument, evidence and citation consistency in a research paper."),
        ("thesis-checker", "Thesis Checker", "Is your thesis specific, arguable, and actually supported?"),
        ("dissertation-checker", "Dissertation Checker", "Diagnostic feedback for long-form postgraduate writing."),
        ("essay-grammar-checker", "Essay Grammar Checker", "Grammar and punctuation feedback written for academic work."),
        ("academic-grammar-checker", "Academic Grammar Checker", "Surface-language checks that do not pretend to grade you."),
        ("essay-structure-checker", "Essay Structure Checker", "See whether introduction, thesis, argument and conclusion are in place."),
        ("thesis-statement-checker", "Thesis Statement Checker", "Guided feedback on thesis strength — not an automatic rewrite."),
        ("argument-checker", "Argument Checker", "Map claims, evidence, analysis and missing counterarguments."),
        ("paragraph-checker", "Paragraph Checker", "Topic sentence, evidence, explanation and relevance for each paragraph."),
        ("citation-checker", "Citation Checker", "APA 7, MLA 9, Harvard, Chicago and IEEE consistency checks."),
        ("apa-citation-checker", "APA 7 Citation Checker", "Check in-text citations and reference-list alignment for APA 7."),
        ("mla-citation-checker", "MLA 9 Citation Checker", "Check MLA in-text citations and Works Cited alignment."),
        ("harvard-citation-checker", "Harvard Citation Checker", "Check Harvard-style citations and reference matching."),
        ("grammar-checker", "Grammar Checker for Academic Writing", "Grammar and punctuation feedback written for essays and assignments."),
        ("ai-writing-checker", "AI-Writing Indicator", "A cautious stylistic indicator — never proof that a student used AI."),
        ("essay-checker-ghana", "Essay Checker for Students in Ghana", "Assignment feedback for university and SHS students in Ghana."),
        ("assignment-checker-ghana", "Assignment Checker Ghana", "Check whether your University of Ghana or KNUST-style assignment answers the question."),
        ("essay-checker-nigeria", "Essay Checker for Students in Nigeria", "Academic feedback for Nigerian university assignments."),
        ("assignment-checker-nigeria", "Assignment Checker Nigeria", "Relevance, argument and citation checks for Nigerian coursework."),
        ("essay-checker-kenya", "Essay Checker for Students in Kenya", "Academic writing feedback for Kenyan university students."),
    ]
    for slug, title, desc in seo:
        db.add(
            SeoPage(
                slug=slug,
                title=f"{title} | AcademicCheck AI",
                meta_description=desc,
                heading=title,
                body_markdown=_seo_body(slug, title, desc),
                og_title=title,
                canonical_path=f"/{slug}",
                country="GH" if "ghana" in slug else "NG" if "nigeria" in slug else "KE" if "kenya" in slug else None,
            )
        )

    posts = [
        (
            "how-to-write-a-strong-thesis-statement",
            "How to write a strong thesis statement",
            "A thesis is a contestable answer to the question, not a topic label.",
        ),
        (
            "how-to-answer-evaluate-in-an-essay",
            "How to answer “evaluate” in an essay",
            "Evaluation means judgement against criteria, not a longer description.",
        ),
        (
            "what-does-critically-discuss-mean",
            "What does “critically discuss” mean?",
            "Critical discussion weighs competing views and the quality of evidence.",
        ),
        (
            "how-to-structure-a-university-essay",
            "How to structure a university essay",
            "Introduction, thesis, developed claims, counterargument, and a synthesising conclusion.",
        ),
        (
            "how-to-cite-sources-in-apa-7",
            "How to cite sources in APA 7",
            "Match every in-text citation to a reference, and do not invent sources.",
        ),
        (
            "difference-between-analysis-and-description",
            "Difference between analysis and description",
            "Description says what happened. Analysis explains significance and relationship.",
        ),
        (
            "pre-submission-essay-checklist",
            "Pre-submission essay checklist (printable mental model)",
            "Question fit, thesis, evidence, structure, citations — in that order.",
        ),
        (
            "how-to-revise-using-feedback",
            "How to revise an essay using feedback (without rewriting everything)",
            "Prioritise question fit and thesis before polishing sentences.",
        ),
        (
            "citation-styles-compared",
            "APA vs MLA vs Harvard: which citation style do you need?",
            "A plain-English comparison so you stop mixing styles mid-essay.",
        ),
        (
            "using-ai-responsibly-for-essays",
            "Using AI responsibly while writing essays",
            "Study aid vs ghostwriting — stay on the right side of integrity policies.",
        ),
        (
            "what-academiccheck-report-means",
            "How to read an AcademicCheck report",
            "Scores are diagnostics. Priority fixes are the useful part.",
        ),
        (
            "assignment-checker-vs-grammar-checker",
            "Assignment checker vs grammar checker: what’s the difference?",
            "Grammar tools polish sentences. Assignment checkers test whether you answered the brief.",
        ),
    ]
    now = datetime.now(UTC)
    for slug, title, excerpt in posts:
        db.add(
            BlogPost(
                slug=slug,
                title=title,
                excerpt=excerpt,
                body_markdown=_blog_body(title, excerpt),
                published_at=now,
            )
        )

    faqs = [
        ("How do I check an assignment?", "Paste or upload your draft, add the assignment question, choose your academic level and citation style, then start analysis.", "product"),
        ("Is the score my real grade?", "No. The score is an AI-assisted diagnostic indicator, not an official academic grade.", "integrity"),
        ("Will this write my assignment?", "No. AcademicCheck AI explains weaknesses and teaching points. It does not generate a full assignment for submission.", "integrity"),
        ("Do you use my work to train AI models?", "Not by default. You can opt in. We do not sell student documents.", "privacy"),
        ("Which files can I upload?", "PDF, DOCX, TXT and Markdown in the MVP. File signatures are checked; the extension alone is not trusted.", "product"),
        ("What do AI-writing indicators mean?", "They are uncertain stylistic signals. They are not proof that a student used AI.", "integrity"),
        ("Can citation verification be wrong?", "Yes. We may fail to find a legitimate source. Inability to verify is not proof of fabrication.", "integrity"),
    ]
    for i, (q, a, cat) in enumerate(faqs):
        db.add(FAQ(question=q, answer=a, category=cat, sort_order=i))


def _seo_body(slug: str, title: str, desc: str) -> str:
    extra = ""
    if "ghana" in slug:
        extra = (
            "\n\nStudents in Ghana often write compare-and-evaluate essays for University of Ghana, KNUST, UCC, "
            "and other institutions. Command words such as *discuss*, *examine* and *assess* usually require a judgement, "
            "not a summary of lecture notes. This page is local guidance, not an official university tool."
        )
    if "nigeria" in slug:
        extra = (
            "\n\nCoursework at Nigerian universities frequently asks you to *critically discuss* or *evaluate* a policy or theory. "
            "A complete answer usually needs a clear thesis, evidence, and engagement with more than one view."
        )
    if "kenya" in slug:
        extra = (
            "\n\nKenyan university essays often combine theory with local examples. Make the examples serve the argument, "
            "and keep citations consistent with the style your department requires."
        )
    return f"""# {title}

{desc}

AcademicCheck AI analyses your work against the assignment question, then shows what appears strong, what appears weak, and what to fix first.

## What this checker does

- Interprets command words such as compare, evaluate, and critically discuss
- Checks whether the draft appears to answer the question
- Reviews thesis, argument, evidence, structure, academic writing, and citations
- Gives priority actions instead of 100 minor nits

## What it does not do

- It does not write the assignment for you
- It does not invent references or quotations
- It does not promise a grade
- It does not treat an AI-writing indicator as proof of misconduct

Always follow your institution’s academic-integrity policy.
{extra}
"""


def _blog_body(title: str, excerpt: str) -> str:
    return f"""# {title}

{excerpt}

Markers are usually looking for a clear answer to the question, supported by reasoning and evidence. Start with the command words. If the question says *evaluate*, description alone is not enough — you need a judgement and the criteria behind it.

When you revise, change one high-impact weakness at a time: thesis, missing evaluation, or unsupported claims. Then re-check. Improvement is easier to see when drafts are compared.

AcademicCheck AI can help you see those weaknesses. It cannot replace reading, thinking, or your institution’s rules.
"""
