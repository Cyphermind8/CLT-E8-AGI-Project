# FILE: gated_loop.py
#!/usr/bin/env python3
"""
Gated micro-transform loop with atomic writes and AST safety checks.

Safe, deterministic edits only (function set must remain identical):
- add a MODULE docstring if missing,
- add __all__ = [] if missing,
- add a one-line header banner comment if missing,
- add a main-guard stub if missing (if __name__ == "__main__": pass),
- add a one-line function docstring if missing,
- add a benign guarded print in main(),
- add a simple empty-input guard on the first arg.

One tiny change per run (PATCH_LINES_BUDGET, default=1).
Atomic writes with timestamped backups to ./backup.
"""

from __future__ import annotations

import argparse, ast, os, sys, time, textwrap
from pathlib import Path
from typing import List, Tuple, Optional

GATED_LOOP_VERSION = "2025-09-17b-ascii"  # version sentinel

def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--path", default="", help="Target file to mutate")
    parser.add_argument("--cycle", type=int, default=0, help="Cycle number for logging")
    parser.add_argument("--strict", action="store_true", help="Strict mode (no external planner)")
    args, _unknown = parser.parse_known_args(argv)
    return args

def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""

def ensure_trailing_newline(s: str) -> str:
    return s if s.endswith("\n") else s + "\n"

def write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    backup_dir = Path("backup"); backup_dir.mkdir(exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    if path.exists():
        (backup_dir / f"{path.name}_{ts}").write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(content, encoding="utf-8")
    os.replace(tmp_path, path)

def list_functions(src: str) -> List[str]:
    try:
        tree = ast.parse(src)
    except Exception:
        return []
    return [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]

def has_module_docstring(src: str) -> bool:
    try:
        tree = ast.parse(src)
    except Exception:
        return False
    return bool(ast.get_docstring(tree))

def has_dunder_all(src: str) -> bool:
    try:
        tree = ast.parse(src)
    except Exception:
        return True
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "__all__":
                    return True
    return False

def has_main_guard(src: str) -> bool:
    try:
        tree = ast.parse(src)
    except Exception:
        return False
    for node in tree.body:
        if isinstance(node, ast.If):
            test = node.test
            if (isinstance(test, ast.Compare) and isinstance(test.left, ast.Name)
                and test.left.id == "__name__"):
                return True
    return False

def find_function_bounds(src: str, func: str) -> Optional[Tuple[int, int, ast.FunctionDef]]:
    try:
        tree = ast.parse(src)
    except Exception:
        return None
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == func:
            lines = src.splitlines(keepends=True)
            start = sum(len(l) for l in lines[: n.lineno - 1])
            end_line = getattr(n, "end_lineno", None)
            end = len(src) if end_line is None else sum(len(l) for l in lines[: end_line])
            return start, end, n
    return None

# ----- Top-level transforms -----

def add_module_docstring_if_missing(src: str) -> tuple[str, bool]:
    if has_module_docstring(src):
        return src, False
    lines = src.splitlines(keepends=True)
    insert_at = 0
    if lines and lines[0].startswith("#!"):
        insert_at = 1
    if len(lines) > insert_at and "coding" in lines[insert_at]:
        insert_at += 1
    # Add an extra blank line after the docstring for CRLF edge-cases and readability
    doc = '""" Auto-added module docstring (CLT-E8 gated loop). """\n\n'
    return "".join(lines[:insert_at] + [doc] + lines[insert_at:]), True

def add_dunder_all_if_missing(src: str) -> tuple[str, bool]:
    if has_dunder_all(src):
        return src, False
    try:
        tree = ast.parse(src)
    except Exception:
        return src, False
    lines = src.splitlines(keepends=True)
    insert_at = 0
    if lines and lines[0].startswith("#!"):
        insert_at = 1
    if (tree.body and isinstance(tree.body[0], ast.Expr)
        and isinstance(getattr(tree.body[0], "value", None), ast.Constant)
        and isinstance(tree.body[0].value.value, str)):
        insert_at = getattr(tree.body[0], "end_lineno", 1)
    stmt = "__all__ = []\n"
    return "".join(lines[:insert_at] + [stmt] + lines[insert_at:]), True

def add_header_banner_if_missing(src: str) -> tuple[str, bool]:
    if "CLT-E8 normalized header" in src:
        return src, False
    lines = src.splitlines(keepends=True)
    insert_at = 0
    if lines and lines[0].startswith("#!"):
        insert_at = 1
    try:
        tree = ast.parse(src)
        if (tree.body and isinstance(tree.body[0], ast.Expr)
            and isinstance(getattr(tree.body[0], "value", None), ast.Constant)
            and isinstance(tree.body[0].value.value, str)):
            insert_at = max(insert_at, getattr(tree.body[0], "end_lineno", 1))
    except Exception:
        pass
    banner = "# CLT-E8 normalized header\n\n"
    return "".join(lines[:insert_at] + [banner] + lines[insert_at:]), True

def add_main_guard_if_missing(src: str) -> tuple[str, bool]:
    if has_main_guard(src):
        return src, False
    base = ensure_trailing_newline(src)
    return base + '\nif __name__ == "__main__":\n    pass\n', True

# ----- Function-level transforms -----

def add_docstring_if_missing(src: str, func: str, one_liner: str) -> tuple[str, bool]:
    b = find_function_bounds(src, func)
    if not b:
        return src, False
    start, end, fn_node = b
    body = src[start:end]
    try:
        fn_module = ast.parse(body)
        fn_def = next(n for n in ast.walk(fn_module) if isinstance(n, ast.FunctionDef))
    except Exception:
        return src, False
    has_doc = (fn_def.body and isinstance(fn_def.body[0], ast.Expr)
               and isinstance(getattr(fn_def.body[0], "value", None), ast.Constant)
               and isinstance(getattr(fn_def.body[0].value, "value", None), str))
    if has_doc:
        return src, False
    lines = body.splitlines(keepends=True)
    indent_spaces = " " * (fn_node.col_offset + 4)
    doc = f'{indent_spaces}""" {one_liner} """\n'
    new_body = "".join(lines[:1] + [doc] + lines[1:])
    return src[:start] + new_body + src[end:], True

def add_guarded_print_at_top(src: str, func: str, print_stmt: str) -> tuple[str, bool]:
    b = find_function_bounds(src, func)
    if not b:
        return src, False
    start, end, fn_node = b
    body = src[start:end]
    try:
        fn_module = ast.parse(body)
        fn_def = next(n for n in ast.walk(fn_module) if isinstance(n, ast.FunctionDef))
    except Exception:
        return src, False
    lines = body.splitlines(keepends=True)
    insert_at = 1
    if (fn_def.body and isinstance(fn_def.body[0], ast.Expr)
        and isinstance(getattr(fn_def.body[0], "value", None), ast.Constant)
        and isinstance(getattr(fn_def.body[0].value, "value", None), str)):
        insert_at = 2
    indent_spaces = " " * (fn_node.col_offset + 4)
    stmt = f"{indent_spaces}{print_stmt}\n"
    if any(print_stmt in l for l in lines):
        return src, False
    new_body = "".join(lines[:insert_at] + [stmt] + lines[insert_at:])
    return src[:start] + new_body + src[end:], True

def add_empty_guard(src: str, func: str) -> tuple[str, bool]:
    b = find_function_bounds(src, func)
    if not b:
        return src, False
    start, end, fn_node = b
    body = src[start:end]
    try:
        fn_module = ast.parse(body)
        fn_def = next(n for n in ast.walk(fn_module) if isinstance(n, ast.FunctionDef))
    except Exception:
        return src, False
    if not fn_def.args.args:
        return src, False
    first = fn_def.args.args[0].arg
    indent_spaces = " " * (fn_node.col_offset + 4)
    guard = (f"{indent_spaces}if {first} is None or "
             f"(isinstance({first}, str) and not {first}.strip()):\n"
             f"{indent_spaces}    return ''\n")
    lines = body.splitlines(keepends=True)
    insert_at = 1
    if (fn_def.body and isinstance(fn_def.body[0], ast.Expr)
        and isinstance(getattr(fn_def.body[0], "value", None), ast.Constant)
        and isinstance(getattr(fn_def.body[0].value, "value", None), str)):
        insert_at = 2
    if any("is None" in l and first in l for l in lines):
        return src, False
    new_body = "".join(lines[:insert_at] + [guard] + lines[insert_at:])
    return src[:start] + new_body + src[end:], True

# ----- Safety gate (now with diagnostics) -----

def _func_names(tree: ast.AST) -> List[str]:
    return sorted(n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))

def ast_safe_after_edit(before: str, after: str) -> tuple[bool, str]:
    try:
        bef = ast.parse(before)
    except Exception as e:
        return False, f"BEFORE parse error: {e!r}"
    try:
        aft = ast.parse(after)
    except Exception as e:
        # show a little context to help debug
        head = "\\n".join(after.splitlines()[:6])
        return False, f"AFTER parse error: {e!r}; after head:\\n{head}"
    nb, na = _func_names(bef), _func_names(aft)
    if nb != na:
        return False, f"function-set mismatch: before={nb} after={na}"
    return True, "ok"

# ----- Plan / main -----

def choose_menu_transforms(path: Path, src: str):
    funcs = list_functions(src)
    allowed = funcs[:]
    plans: List[str] = []
    # module-level first
    plans += ["module_docstring", "dunder_all", "header_banner", "main_guard"]
    # function-level by presence
    if "analyze_code" in funcs:
        plans += ["docstring:analyze_code", "add_empty_guard:analyze_code"]
    if "main" in funcs:
        plans += ["entrylog:main"]
    for c in ("validate_improvement", "retrieve_external_knowledge", "execute_code", "fibonacci"):
        if c in funcs:
            plans.append(f"add_empty_guard:{c}")
    return allowed, plans

def apply_one_transform(src: str, plan: str) -> tuple[str, Optional[str]]:
    if plan == "module_docstring":
        new_src, changed = add_module_docstring_if_missing(src)
        return (new_src, plan) if changed else (src, None)
    if plan == "dunder_all":
        new_src, changed = add_dunder_all_if_missing(src)
        return (new_src, plan) if changed else (src, None)
    if plan == "header_banner":
        new_src, changed = add_header_banner_if_missing(src)
        return (new_src, plan) if changed else (src, None)
    if plan == "main_guard":
        new_src, changed = add_main_guard_if_missing(src)
        return (new_src, plan) if changed else (src, None)
    if plan.startswith("docstring:"):
        fn = plan.split(":", 1)[1]
        new_src, changed = add_docstring_if_missing(src, fn, f"Auto-added docstring for {fn}()")
        return (new_src, plan) if changed else (src, None)
    if plan == "entrylog:main":
        new_src, changed = add_guarded_print_at_top(src, "main", 'print("[=] entry: main")')
        return (new_src, plan) if changed else (src, None)
    if plan.startswith("add_empty_guard:"):
        fn = plan.split(":", 1)[1]
        new_src, changed = add_empty_guard(src, fn)
        return (new_src, plan) if changed else (src, None)
    return src, None

def main(argv: List[str]) -> int:
    t0 = time.time()
    args = parse_args(argv)
    cycle = args.cycle or 0
    candidates = [Path("code_analysis.py"), Path("eval_loop.py"), Path("safe_code_modification.py"), Path("ai_core.py")]
    path = Path(args.path) if args.path else candidates[cycle % len(candidates)]
    print(f"[CYCLE {cycle}] starting...")
    src = read_text(path)
    if not src:
        print("[=] No source loaded; exiting with no-op.")
        print(f"[CYCLE {cycle}] duration={time.time()-t0:.1f}s exit=0")
        return 0
    allowed, plans = choose_menu_transforms(path, src)
    print(f"[=] AllowedFunctions: {allowed!r}")
    budget = int(os.getenv("PATCH_LINES_BUDGET", "1"))
    applied: List[str] = []
    new_src = src
    for plan in plans:
        if len(applied) >= budget:
            break
        after, label = apply_one_transform(new_src, plan)
        if label and after != new_src:
            after = ensure_trailing_newline(after)
            ok, reason = ast_safe_after_edit(new_src, after)
            if not ok:
                print(f"[!] Edit rejected by AST safety gate: {label!r} | reason: {reason}")
                # peek at the after head to aid debugging
                head = "\\n".join(after.splitlines()[:6])
                print(textwrap.indent(f"after head:\\n{head}", prefix="[debug] "))
                continue
            new_src = after
            applied.append(label)
    if applied and new_src != src:
        write_atomic(path, new_src)
        print(f"[+] Applied: {applied!r}")
    else:
        print("[=] No safe improvement proposed (empty edits).")
    print(f"[CYCLE {cycle}] duration={time.time()-t0:.1f}s exit=0")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
