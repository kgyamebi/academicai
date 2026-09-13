"""Pass-2 evidence: SEO sitemap covers seeded product slugs (REQ-64 / REQ-68)."""

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SITEMAP = REPO / "frontend" / "app" / "sitemap.ts"
SEED = REPO / "backend" / "app" / "seed.py"

REQUIRED_SEO_SLUGS = [
    "ai-essay-checker",
    "assignment-checker",
    "essay-checker",
    "academic-writing-checker",
    "ai-assignment-checker",
    "research-paper-checker",
    "thesis-checker",
    "dissertation-checker",
    "essay-grammar-checker",
    "academic-grammar-checker",
    "essay-structure-checker",
    "thesis-statement-checker",
    "argument-checker",
    "paragraph-checker",
    "citation-checker",
    "apa-citation-checker",
    "mla-citation-checker",
    "harvard-citation-checker",
    "ai-writing-checker",
    "grammar-checker",
]


def test_sitemap_includes_all_req64_seo_slugs():
    text = SITEMAP.read_text(encoding="utf-8")
    missing = [slug for slug in REQUIRED_SEO_SLUGS if f'"{slug}"' not in text]
    assert missing == [], f"sitemap.ts missing SEO slugs: {missing}"


def test_seed_defines_same_seo_slugs():
    text = SEED.read_text(encoding="utf-8")
    missing = [slug for slug in REQUIRED_SEO_SLUGS if f'"{slug}"' not in text]
    assert missing == [], f"seed.py missing SEO slugs: {missing}"


def test_help_page_emits_faq_json_ld_when_faqs_exist():
    help_page = (REPO / "frontend" / "app" / "help" / "page.tsx").read_text(encoding="utf-8")
    assert "FAQPage" in help_page
    assert "application/ld+json" in help_page
