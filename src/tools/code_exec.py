# FILE: src/tools/code_exec.py
from __future__ import annotations
import builtins

SAFE_BUILTINS = {"range": range, "sum": sum, "min": min, "max": max, "len": len, "abs": abs, "all": all, "any": any}
def run(code: str):
    # disallow import/exec/eval/open
    bad = ("__import__", "import ", "open(", "exec(", "eval(")
    if any(b in code for b in bad):
        raise ValueError("Disallowed in sandbox")
    g = {"__builtins__": SAFE_BUILTINS}
    l: dict = {}
    exec(code, g, l)
    return l.get("result") if "result" in l else l.popitem()[1] if l else None