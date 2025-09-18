# microedit.py  —  Python 3.8-compatible
# Minimal, battle-tested utilities for safe micro-edits (guard insertion).
# Keeps the public API that gated_loop.py imports: make_guard_patch(...)

import ast
import os
import textwrap
from typing import List

PATCH_LINES_BUDGET = int(os.getenv("PATCH_LINES_BUDGET", "60")).__int__()


def _line_count(s: str) -> int:
    return s.count("\n") + (0 if s.endswith("\n") else 1)


def _get_fn_node(module_text: str, fn_name: str):
    """
    Return the ast.FunctionDef node for fn_name (top-level only), else None.
    """
    try:
        tree = ast.parse(module_text)
    except Exception:
        return None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == fn_name:
            return node
    return None


def _fn_source(module_text: str, fn_node: ast.FunctionDef) -> str:
    """
    Extract the original source for the function from the module text.
    Uses lineno/end_lineno (3.8+ has end_lineno set by parser).
    """
    # ast nodes are 1-indexed
    start = getattr(fn_node, "lineno", None)
    end = getattr(fn_node, "end_lineno", None)
    if start is None or end is None:
        # Fallback: reconstruct via text slicing if end_lineno not present
        lines = module_text.splitlines(True)
        # naive scan to the next top-level def/class
        i = start - 1
        j = i + 1
        while j < len(lines):
            line = lines[j]
            if line and (line[0] not in (" ", "\t")) and line.lstrip().startswith(("def ", "class ")):
                break
            j += 1
        return "".join(lines[i:j])
    lines = module_text.splitlines(True)
    return "".join(lines[start - 1 : end])


def _first_param(fn_node: ast.FunctionDef) -> str:
    """
    Return the first *positional* parameter name for guard insertion.
    We prefer the first "real" argument (skip self/cls if present).
    """
    args = [a.arg for a in fn_node.args.args]
    if not args:
        return ""
    if args[0] in ("self", "cls") and len(args) > 1:
        return args[1]
    return args[0]


def _get_indentation(fn_src: str) -> str:
    """
    Determine the indentation used inside the function body.
    Default to 4 spaces if we can't infer it.
    """
    for line in fn_src.splitlines():
        # Find the first indented, non-empty line after the 'def'
        if line.startswith("def "):
            continue
        if line.strip() == "":
            continue
        leading = line[: len(line) - len(line.lstrip())]
        if leading:
            return leading
    return "    "


def _has_early_empty_guard(fn_node: ast.FunctionDef, first_param: str) -> bool:
    """
    Heuristic: detect an early 'if not <param>: return ...' within the first few statements.
    We only scan the top one or two statements to avoid heavy analysis.
    """
    body = getattr(fn_node, "body", [])
    if not body:
        return False
    candidates = body[:2]
    for stmt in candidates:
        if isinstance(stmt, ast.If):
            # check condition is 'not <param>'
            test = stmt.test
            if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not) and isinstance(test.operand, ast.Name):
                if test.operand.id == first_param:
                    # and immediate return in body
                    for b in stmt.body:
                        if isinstance(b, ast.Return):
                            return True
    return False


def _inject_after_docstring(fn_src: str, guard_lines: List[str]) -> str:
    """
    Insert guard lines immediately after the docstring block if present,
    otherwise after the function signature line.
    """
    lines = fn_src.splitlines(True)
    if not lines:
        return fn_src

    # find the signature line index
    sig_idx = 0
    for i, line in enumerate(lines):
        if line.lstrip().startswith("def "):
            sig_idx = i
            break

    # detect docstring block start/end (very simple heuristic)
    body_idx = sig_idx + 1
    # skip blank lines
    while body_idx < len(lines) and lines[body_idx].strip() == "":
        body_idx += 1

    # if the first non-blank line is a string literal (docstring)
    has_doc = False
    if body_idx < len(lines):
        stripped = lines[body_idx].lstrip()
        if stripped.startswith(('"""', "'''")):
            quote = '"""' if stripped.startswith('"""') else "'''"
            has_doc = True
            # advance until docstring closing line
            j = body_idx
            # if single-line docstring like """foo"""
            if stripped.count(quote) >= 2:
                body_idx = j + 1
            else:
                j += 1
                while j < len(lines):
                    if quote in lines[j]:
                        body_idx = j + 1
                        break
                    j += 1

    indent = _get_indentation(fn_src)
    injected = [indent + g + ("\n" if not g.endswith("\n") else "") for g in guard_lines]

    # Insert after docstring (if any), else after signature block and blank lines
    new_lines = lines[:body_idx] + injected + lines[body_idx:]
    return "".join(new_lines)


def _make_replace_patch(scope_file: str, fn_name: str, new_fn_src: str, intent: str = "add_guard") -> dict:
    return {
        "type": "patch",
        "intent": intent,
        "scope": {"file": scope_file},
        "edits": [{"loc": {"function": fn_name}, "content": new_fn_src}],
        # Keep the same constraint style the rest of your stack expects
        "constraints": {"max_lines_changed": PATCH_LINES_BUDGET},
    }


def make_guard_patch(module_text: str, scope_file: str, fn_name: str, empty_return: str = '""'):
    """
    Build a safe patch that adds:
        if not <first_param>:
            return <empty_return>

    • Respects PATCH_LINES_BUDGET.
    • Skips functions with no positional params.
    • Skips if an early guard already exists.
    • Injects right after the docstring when present.
    """
    node = _get_fn_node(module_text, fn_name)
    if not node:
        return None

    orig_src = _fn_source(module_text, node)
    if _line_count(orig_src) > PATCH_LINES_BUDGET:
        return None

    param = _first_param(node)
    if not param:
        return None

    if _has_early_empty_guard(node, param):
        return None

    guard = [f"if not {param}:", f"    return {empty_return}"]
    new_src = _inject_after_docstring(orig_src, guard)

    if _line_count(new_src) > PATCH_LINES_BUDGET:
        return None

    return _make_replace_patch(scope_file, fn_name, new_src, intent="add_guard")
