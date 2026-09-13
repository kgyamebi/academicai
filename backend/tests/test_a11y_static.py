import re
from pathlib import Path

FRONTEND = Path(__file__).resolve().parents[2] / "frontend"
PAGES = FRONTEND / "app"
FIXTURES = FRONTEND / "a11y" / "fixtures"


def test_interactive_controls_declare_a_type():
    offenders = []
    for path in FRONTEND.rglob("*.tsx"):
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(r"<button\b([^>]*?)>", text, re.DOTALL):
            if "type=" not in match.group(1):
                line = text[: match.start()].count("\n") + 1
                offenders.append(f"{path.relative_to(FRONTEND)}:{line}")
    assert not offenders, "Buttons must set type=button or type=submit\n" + "\n".join(offenders)


def test_skip_link_and_lang_exist():
    layout = (PAGES / "layout.tsx").read_text(encoding="utf-8")
    assert 'lang="en"' in layout
    assert "Skip to main content" in layout
    assert 'href="#main-content"' in layout
    assert 'id="main-content">{children}' not in layout.replace(" ", "")


def test_authenticated_shell_owns_skip_target():
    app_layout = (PAGES / "app" / "layout.tsx").read_text(encoding="utf-8")
    assert 'id="main-content"' in app_layout
    assert "Escape" in (FRONTEND / "components" / "SiteHeader.tsx").read_text(encoding="utf-8")


def test_contrast_token_is_defined():
    css = (PAGES / "globals.css").read_text(encoding="utf-8")
    assert "--ink-muted:" in css
    assert "--teal:" in css
    assert "--crimson:" in css


def test_no_low_contrast_ink_opacity():
    offenders = []
    for path in FRONTEND.rglob("*.tsx"):
        text = path.read_text(encoding="utf-8")
        if "text-[var(--ink)]/" in text:
            offenders.append(str(path.relative_to(FRONTEND)))
    assert not offenders, "Use --ink-muted instead of ink opacity utilities:\n" + "\n".join(offenders)


def test_required_surfaces_have_main_or_heading():
    required = [
        PAGES / "page.tsx",
        PAGES / "pricing" / "page.tsx",
        PAGES / "app" / "dashboard" / "page.tsx",
        PAGES / "app" / "billing" / "page.tsx",
        PAGES / "app" / "settings" / "page.tsx",
        PAGES / "app" / "admin" / "page.tsx",
        PAGES / "app" / "coach" / "page.tsx",
        PAGES / "app" / "assignments" / "[id]" / "page.tsx",
        PAGES / "app" / "assignments" / "[id]" / "report" / "page.tsx",
        PAGES / "check" / "page.tsx",
    ]
    missing = [
        str(path.relative_to(FRONTEND))
        for path in required
        if "<main" not in path.read_text(encoding="utf-8") and "<h1" not in path.read_text(encoding="utf-8")
    ]
    assert not missing, "Core pages need a main landmark or h1:\n" + "\n".join(missing)


def test_forms_associate_errors_and_labels():
    login = (PAGES / "login" / "page.tsx").read_text(encoding="utf-8")
    check = (PAGES / "check" / "page.tsx").read_text(encoding="utf-8")
    coach = (PAGES / "app" / "coach" / "page.tsx").read_text(encoding="utf-8")
    billing = (PAGES / "app" / "billing" / "page.tsx").read_text(encoding="utf-8")
    assert 'role="alert"' in login
    assert "htmlFor=" in check and 'id="question"' in check
    assert 'htmlFor="assignment_id"' in coach
    assert 'role="alert"' in billing


def test_findings_are_not_color_only():
    card = (FRONTEND / "components" / "FindingCard.tsx").read_text(encoding="utf-8")
    assert "sr-only" in card
    assert "AlertTriangle" in card or "AlertOctagon" in card


def test_editor_toolbar_is_labelled():
    editor = (FRONTEND / "components" / "Editor.tsx").read_text(encoding="utf-8")
    assert 'role="toolbar"' in editor
    assert "aria-pressed" in editor
    assert "aria-keyshortcuts" in editor
    assert "Assignment draft" in editor


def test_no_native_confirm_dialogs():
    settings = (PAGES / "app" / "settings" / "page.tsx").read_text(encoding="utf-8")
    assert "window.confirm" not in settings
    assert "confirm(" not in settings
    assert 'role="alertdialog"' in settings
    assert "Tab" in settings
    assert "confirmDeleteRef" in settings


def test_reduced_motion_and_hit_targets_defined():
    css = (PAGES / "globals.css").read_text(encoding="utf-8")
    assert "prefers-reduced-motion" in css
    assert ".ac-hit" in css
    assert "min-height: 44px" in css


def test_compare_uses_a_table():
    versions = (PAGES / "app" / "assignments" / "[id]" / "versions" / "page.tsx").read_text(encoding="utf-8")
    assert "<table" in versions
    assert "<pre" not in versions


def test_report_scores_use_a_table():
    report = (PAGES / "app" / "assignments" / "[id]" / "report" / "page.tsx").read_text(encoding="utf-8")
    assert "<table" in report
    assert "<caption" in report


def test_axe_fixtures_cover_required_surfaces():
    expected = {
        "landing.html",
        "pricing.html",
        "features.html",
        "help.html",
        "dashboard.html",
        "workspace.html",
        "report.html",
        "versions.html",
        "coach.html",
        "billing.html",
        "settings.html",
        "admin.html",
        "editor.html",
        "login.html",
    }
    present = {path.name for path in FIXTURES.glob("*.html")}
    missing = expected - present
    assert not missing, f"Missing axe fixtures: {missing}"
    assert (FRONTEND / "a11y" / "scan.mjs").exists()
