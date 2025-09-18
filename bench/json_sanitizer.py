from __future__ import annotations
# FILE: bench/json_sanitizer.py
"""
Relaxed JSON parsing for flaky LLM outputs.

Tolerates:
- ```json ...``` fences
- BOM/whitespace
- smart quotes
- trailing commas
- extra text before/after the JSON block

Usage:
    from bench.json_sanitizer import parse_relaxed
    data = parse_relaxed(text)
"""

import json
import re
from typing import Any

_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)
_OBJ_RE = re.compile(r"\{[\s\S]*\}", re.DOTALL)
_ARR_RE = re.compile(r"\[[\s\S]*\]", re.DOTALL)

def _strip_bom(s: str) -> str:
    return s.lstrip("\ufeff")

def _drop_fences(s: str) -> str:
    m = _FENCE_RE.search(s)
    return m.group(1) if m else s

def _extract_largest_json_block(s: str) -> str | None:
    cands = []
    for rx in (_OBJ_RE, _ARR_RE):
        cands += [m.group(0) for m in rx.finditer(s)]
    if not cands:
        return None
    return max(cands, key=len)

def _tiny_repairs(s: str) -> str:
    # normalize smart quotes
    s = (s.replace("\u201c", '"').replace("\u201d", '"')
           .replace("\u2018", '"').replace("\u2019", '"'))
    # remove trailing commas
    s = re.sub(r",\s*([}\]])", r"\1", s)
    return s

def parse_relaxed(text: str) -> Any:
    # 1) raw
    try:
        return json.loads(text)
    except Exception:
        pass
    # 2) strip fence/BOM
    cleaned = _strip_bom(_drop_fences(text)).strip()
    try:
        return json.loads(cleaned)
    except Exception:
        pass
    # 3) extract/repair
    block = _extract_largest_json_block(cleaned)
    if block:
        return json.loads(_tiny_repairs(block))
    raise json.JSONDecodeError("No parseable JSON found", text, 0)
