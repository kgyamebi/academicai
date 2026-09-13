"""CI gate: fail if backend app code reintroduces bare prints or silent except/pass."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "app"


def _silent_except_problems() -> list[str]:
    problems: list[str] = []
    for path in ROOT.rglob("*.py"):
        rel = str(path.relative_to(ROOT.parent))
        src = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(src, filename=str(path))
        except SyntaxError as exc:
            problems.append(f"{rel}: syntax error {exc}")
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print":
                if path.name == "emailer.py":
                    continue
                problems.append(f"{rel}:{node.lineno}: bare print()")
            if isinstance(node, ast.ExceptHandler) and len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                # Optional dependency ImportError is allowed.
                if node.type and isinstance(node.type, ast.Name) and node.type.id == "ImportError":
                    continue
                problems.append(f"{rel}:{node.lineno}: silent except/pass")
    return problems


def test_no_bare_print_or_silent_except_pass():
    problems = _silent_except_problems()
    assert problems == [], "Logging hygiene violations:\n" + "\n".join(problems)
