# FILE: src/tools/json_tools_v1.py
"""
JSON tool shims to remove brittleness from LLM prompts and stabilize benches.

Exports (pure functions, deterministic):
- sort_json_values(obj): recursively sort lists (by JSON-serialized value) and dict keys.
- json_merge(left, right, mode): merge two JSON structures with clear conflict rules.

Design principles
-----------------
• No third-party deps; consistent behavior across runs.
• "JSON-only" thinking: avoid side effects, accept/return Python data that is JSON-safe.
• Deterministic ordering via JSON dumps to ensure stable equality checks.
"""

from __future__ import annotations
from typing import Any
import json

def _as_json_key(x: Any) -> str:
    # Deterministic key for sorting heterogenous values
    return json.dumps(x, sort_keys=True, ensure_ascii=False)

def _sort_obj(x: Any) -> Any:
    if isinstance(x, dict):
        # Sort by key (string compare)
        return {k: _sort_obj(v) for k, v in sorted(x.items(), key=lambda kv: kv[0])}
    if isinstance(x, list):
        # Sort each element after normalizing recursively, then sort by JSON form
        normalized = [_sort_obj(e) for e in x]
        return sorted(normalized, key=_as_json_key)
    # primitive
    return x

def sort_json_values(obj: Any) -> Any:
    """
    Recursively sort dict keys and list contents.
    For lists, uses JSON-string form to compare across types deterministically.
    """
    return _sort_obj(obj)

class MergeError(Exception):
    pass

def _merge_values(a: Any, b: Any, mode: str) -> Any:
    """Internal merge with three modes:
       - 'prefer_right': right wins on conflicts
       - 'prefer_left' : left wins on conflicts
       - 'combine'     : attempt structural union (dict-deep-merge, list union unique by JSON)
    """
    if mode not in ("prefer_right", "prefer_left", "combine"):
        raise MergeError(f"Unknown merge mode: {mode}")

    # Dict x Dict => merge per mode
    if isinstance(a, dict) and isinstance(b, dict):
        keys = set(a) | set(b)
        out = {}
        for k in sorted(keys):
            if k in a and k in b:
                out[k] = _merge_values(a[k], b[k], mode)
            elif k in a:
                out[k] = a[k]
            else:
                out[k] = b[k]
        return out

    # List x List => union or prefer side
    if isinstance(a, list) and isinstance(b, list):
        if mode == "prefer_right":
            return b
        if mode == "prefer_left":
            return a
        # combine: union with deterministic order by JSON key
        seen = set()
        out = []
        for item in a + b:
            key = _as_json_key(item)
            if key not in seen:
                seen.add(key)
                out.append(item)
        return sorted((_sort_obj(e) for e in out), key=_as_json_key)

    # Primitive clash: choose side or prefer_right default
    if mode == "prefer_left":
        return a
    if mode == "prefer_right":
        return b
    # combine on primitives: if equal -> that value; else keep right (explicit rule)
    return b if _as_json_key(a) != _as_json_key(b) else a

def json_merge(left: Any, right: Any, mode: str = "combine") -> Any:
    """
    Merge two JSON-serializable Python values deterministically.

    Modes
    -----
    - prefer_right: right wins on conflicts
    - prefer_left : left wins on conflicts
    - combine     : dict-deep-merge; list union unique; primitive: right wins on difference
    """
    merged = _merge_values(left, right, mode)
    return sort_json_values(merged)
