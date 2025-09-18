from __future__ import annotations
import re, ast, textwrap
from typing import Dict, Any, Tuple

# Only allow function-level replacements (no arbitrary line edits).
ALLOWED_INTENTS = {
    "optimize_loop",
    "add_guard",
    "refactor_function",
    "rename_symbol",
    "remove_dead_code",
}
ALLOWED_OPS = {"replace"}  # function-level only

# ---------------- Normalization helpers ----------------

# Match any fence line made of one-or-more backticks or tildes, optionally with a language tag.
_FENCE_LINES = [
    re.compile(r"^\s*`{1,}\s*(?:python|py)?\s*$", re.IGNORECASE),
    re.compile(r"^\s*~{1,}\s*(?:python|py)?\s*$", re.IGNORECASE),
    re.compile(r"^\s*`{1,}\s*$"),  # pure ticks
    re.compile(r"^\s*~{1,}\s*$"),  # pure tildes
]

def _is_fence_line(s: str) -> bool:
    s = s.rstrip("\r\n")
    for pat in _FENCE_LINES:
        if pat.match(s):
            return True
    return False

def _strip_code_fences(text: str) -> str:
    """
    Remove surrounding Markdown-style code fences if present.
    Accepts single-or-multi backticks or tildes, with/without 'python'.
    """
    t = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = t.splitlines()
    if not lines:
        return ""
    # Strip leading fences
    while lines and _is_fence_line(lines[0]):
        lines = lines[1:]
    # Strip trailing fences
    while lines and _is_fence_line(lines[-1]):
        lines = lines[:-1]
    return "\n".join(lines)

def _strip_inline_outer_fence(text: str) -> str:
    """
    Strip a single inline fence pair around the whole blob, e.g.:
      `def f(): pass`
      ```def f(): pass```
      ~~~def f(): pass~~~
    Only if it looks like Python (decorator or def/async def).
    """
    s = text.strip()
    if not s:
        return s
    first = s[0]
    if first not in ("`", "~"):
        return text
    # prefix fence count
    i = 0
    while i < len(s) and s[i] == first:
        i += 1
    # suffix fence count
    j = len(s) - 1
    while j >= 0 and s[j] == first:
        j -= 1
    inner = s[i:j+1].strip()
    if not inner:
        return text
    looks_py = inner.startswith("@") or inner.startswith("def ") or inner.startswith("async def ") or ("def " in inner)
    return inner if looks_py else text

def _first_nonempty_index(lines: list[str]) -> int:
    for i, ln in enumerate(lines):
        if ln.strip():
            return i
    return -1

def _force_flush_left_first_line(t: str) -> str:
    """
    Ensure the first non-empty line starts at column 0 to avoid 'unexpected indent' at top-level.
    """
    lines = t.splitlines(True)  # keep EOLs
    idx = _first_nonempty_index(lines)
    if idx == -1:
        return t
    lines[idx] = lines[idx].lstrip()
    return "".join(lines)

def _normalize_function_block(content: str) -> str:
    """
    Normalize function text so it can be parsed as a top-level module:
      - remove BOM
      - strip code fences/backticks/tildes (line fences and inline pairs)
      - trim outer blank lines
      - dedent common indentation
      - force first non-empty line to column 0
      - ensure trailing newline
    """
    if not isinstance(content, str):
        return "\n"
    t = content
    if t and t[0] == "\ufeff":  # BOM
        t = t[1:]
    t = _strip_code_fences(t)
    t = _strip_inline_outer_fence(t)
    t = t.strip("\n")
    if not t:
        return "\n"
    t = textwrap.dedent(t)
    t = _force_flush_left_first_line(t)
    if not t.endswith("\n"):
        t += "\n"
    return t

# ---------------- Validation ----------------

def _validate_function_def(content: str, expected_name: str) -> Tuple[bool, str, int]:
    """
    Parse 'content' and ensure it contains exactly one top-level (async) function
    whose name matches expected_name. Returns (ok, reason, line_count).
    """
    text = _normalize_function_block(content)
    # First non-empty line must begin with decorator or def/async def
    for line in text.splitlines():
        if line.strip():
            head = line.strip()
            if not (head.startswith("@") or head.startswith("def ") or head.startswith("async def ")):
                return (False, f"first line must start with '@', 'def', or 'async def' (got: {head!r})", text.count("\n"))
            break
    try:
        mod = ast.parse(text)
    except SyntaxError as e:
        return (False, f"syntax_error: {e}", text.count("\n"))
    fdefs = [n for n in mod.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if len(fdefs) != 1:
        return (False, f"expected exactly one function def, found {len(fdefs)}", text.count("\n"))
    if fdefs[0].name != expected_name:
        return (False, f"function name mismatch: got '{fdefs[0].name}', expected '{expected_name}'", text.count("\n"))
    return (True, "ok", text.count("\n"))

def validate_patch(p: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Schema:
      {
        "type": "patch",
        "intent": "<one of ALLOWED_INTENTS>",
        "scope": {"file": "<str>"},
        "edits": [
          {"op": "replace", "loc": {"function": "<name>"}, "content": "<full def ...>"},
        ],
        "constraints": {"max_lines_changed": <int>}
      }
    Mutates p['edits'][0]['content'] to its normalized form on success.
    """
    for k in ("type", "intent", "scope", "edits"):
        if k not in p:
            return (False, f"missing key: {k}")
    if p["type"] != "patch":
        return (False, "type must be 'patch'")
    if p["intent"] not in ALLOWED_INTENTS:
        return (False, f"intent not allowed: {p['intent']}")
    scope = p["scope"]
    if "file" not in scope or not isinstance(scope["file"], str) or not scope["file"]:
        return (False, "scope.file required and must be non-empty")

    edits = p["edits"]
    if not isinstance(edits, list) or len(edits) != 1:
        return (False, "edits must be a single-item list (function-level replace only)")

    max_lines = int(p.get("constraints", {}).get("max_lines_changed", 80))
    e = edits[0]
    op = e.get("op", "")
    if op not in ALLOWED_OPS:
        return (False, f"op '{op}' not allowed; only 'replace' is permitted")
    loc = e.get("loc", {})
    if not isinstance(loc, dict) or "function" not in loc or not isinstance(loc["function"], str) or not loc["function"]:
        return (False, "loc must specify 'function': '<name>'")
    content = e.get("content", "")
    if not isinstance(content, str) or not content.strip():
        return (False, "content must be a non-empty string containing a full 'def'")

    # Normalize BEFORE parsing; update patch in place so downstream uses clean text.
    norm = _normalize_function_block(content)
    ok, reason, line_count = _validate_function_def(norm, loc["function"])
    if not ok:
        return (False, f"function content invalid: {reason}")
    if line_count > max_lines:
        return (False, f"too many lines changed: {line_count} > {max_lines}")

    e["content"] = norm  # commit normalized text
    return (True, "ok")

# ---------------- Apply ----------------

def apply_patch_to_text(src: str, patch: Dict[str, Any]) -> str:
    """
    Replace the target function definition with the provided (normalized) function block.

    We preserve decorators if the original function has them:
      - Capture optional decorator lines in group(1)
      - Match 'def' or 'async def' for the target function
      - Replace only the function block; keep captured decorators
    """
    e = patch["edits"][0]
    fname = e["loc"]["function"]
    content = e.get("content", "")
    new_block = content if content.endswith("\n") else content + "\n"

    # Optional decorators group(1), then (async )?def fname(...) : body ... up to next top-level def/class or EOF.
    pattern = re.compile(
        rf"(?ms)^((?:@\w[^\r\n]*\r?\n)*)"
        rf"(?:async\s+)?def\s+{re.escape(fname)}\s*\([^)]*\)\s*:\s*(?:\r?\n).*?"
        rf"(?=^(?:@\w[^\r\n]*\r?\n)*(?:async\s+)?def\s+|^class\s+|\Z)"
    )

    if not pattern.search(src):
        raise ValueError(f"target function '{fname}' not found for replacement")

    def _repl(m: re.Match) -> str:
        decorators = m.group(1) or ""
        return decorators + new_block

    return re.sub(pattern, _repl, src, count=1)
