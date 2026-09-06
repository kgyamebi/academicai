import re
from pathlib import Path

FRONTEND = Path(__file__).resolve().parents[2] / "frontend"


def test_interactive_controls_declare_a_type():
    offenders = []
    for path in FRONTEND.rglob("*.tsx"):
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(r"<button\b([^>]*?)>", text, re.S):
            if "type=" not in match.group(1):
                line = text[: match.start()].count("\n") + 1
                offenders.append(f"{path.relative_to(FRONTEND)}:{line}")
    assert not offenders, "Buttons must set type=button or type=submit\n" + "\n".join(offenders)


def test_skip_link_and_lang_exist():
    layout = (FRONTEND / "app" / "layout.tsx").read_text(encoding="utf-8")
    assert 'lang="en"' in layout
    assert "Skip to main content" in layout
    assert "main-content" in layout


def test_contrast_token_is_defined():
    css = (FRONTEND / "app" / "globals.css").read_text(encoding="utf-8")
    assert "--ink-muted:" in css
    assert "--teal:" in css


def test_no_low_contrast_ink_opacity():
    offenders = []
    for path in FRONTEND.rglob("*.tsx"):
        text = path.read_text(encoding="utf-8")
        if "text-[var(--ink)]/" in text:
            offenders.append(str(path.relative_to(FRONTEND)))
    assert not offenders, "Use --ink-muted instead of ink opacity utilities:\n" + "\n".join(offenders)


def test_required_surfaces_have_main_or_heading():
    required = [
        FRONTEND / "app" / "page.tsx",
        FRONTEND / "app" / "app" / "dashboard" / "page.tsx",
        FRONTEND / "app" / "app" / "billing" / "page.tsx",
        FRONTEND / "app" / "app" / "assignments" / "[id]" / "report" / "page.tsx",
        FRONTEND / "app" / "app" / "admin" / "page.tsx",
        FRONTEND / "app" / "check" / "page.tsx",
    ]
    missing = [str(path.relative_to(FRONTEND)) for path in required if "<main" not in path.read_text(encoding="utf-8") and "<h1" not in path.read_text(encoding="utf-8")]
    assert not missing, "Core pages need a main landmark or h1:\n" + "\n".join(missing)
