# FILE: tests/test_no_heavy_imports.py
"""
Fail fast if heavyweight imports show up in core CI targets.

Blocked by default:
- torch
- transformers
- tensorflow
- jax
- accelerate
- bitsandbytes

Add others here if needed.
"""

from __future__ import annotations

import ast
from pathlib import Path

BLOCKED = {
    "torch",
    "transformers",
    "tensorflow",
    "jax",
    "accelerate",
    "bitsandbytes",
}

# Keep the list small and explicit for now
TARGETS = [
    Path("code_analysis.py"),
    Path("gated_loop.py"),
    Path("eval_loop.py"),
    Path("safe_code_modification.py"),
]


def _imports_in(source: str) -> set[str]:
    try:
        tree = ast.parse(source)
    except Exception:
        # If it doesn't even parse, let other tests catch that;
        # this test's job is only to guard imports.
        return set()
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                root = (n.name or "").split(".", 1)[0]
                if root:
                    found.add(root)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            root = mod.split(".", 1)[0] if mod else ""
            if root:
                found.add(root)
    return found


def test_no_blocked_imports():
    offenders: dict[str, set[str]] = {}
    for path in TARGETS:
        if not path.exists():
            continue
        mods = _imports_in(path.read_text(encoding="utf-8"))
        bad = mods & BLOCKED
        if bad:
            offenders[str(path)] = bad

    assert not offenders, (
        "Blocked heavy imports detected. "
        f"Offenders: {offenders}. Remove these modules from the listed files."
    )
