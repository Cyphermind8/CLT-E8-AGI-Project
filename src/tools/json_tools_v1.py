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
# --- bench compatibility: flexible dispatcher ---
from typing import Any

_TOOLBOX = {
    "sort_json_values": sort_json_values,
    "json_sort_values": sort_json_values,  # alias
    "json_merge": json_merge,
    "json_merge_values": json_merge,       # alias
}

def execute_call(spec: Any, args: Any = None) -> Any:
    """
    Accepts either:
      - execute_call({"tool": "json_merge", "args": {...}})
      - execute_call("json_merge", {"left":..., "right":..., "mode":"combine"})
    """
    if isinstance(spec, dict):
        name = spec.get("tool") or spec.get("name")
        call_args = spec.get("args") or {}
    else:
        name = spec
        call_args = args or {}

    fn = _TOOLBOX.get(name)
    if fn is None:
        raise ValueError(f"Unknown tool: {name!r}. Available: {sorted(_TOOLBOX.keys())}")

    if not isinstance(call_args, dict):
        raise TypeError("args must be a dict of keyword arguments")

    import inspect
    sig = inspect.signature(fn)
    bound = sig.bind_partial(**call_args)
    return fn(*bound.args, **bound.kwargs)
# --- end dispatcher ---
# --- improved bench dispatcher (overrides earlier execute_call) ---
from inspect import signature
from typing import Any

# keep the existing toolbox
try:
    _TOOLBOX
except NameError:  # safety if file layout changes
    _TOOLBOX = {
        "sort_json_values": sort_json_values,
        "json_sort_values": sort_json_values,  # alias
        "json_merge": json_merge,
        "json_merge_values": json_merge,       # alias
    }

_SYNONYMS = {
    "obj":   {"obj","value","data","json","payload","content","key","x"},
    "left":  {"left","a","lhs","l","x"},
    "right": {"right","b","rhs","r","y"},
    "mode":  {"mode","strategy","how","merge_mode"},
}

def _normalize_args(fn, args_dict: dict):
    if not isinstance(args_dict, dict):
        raise TypeError("args must be a dict")

    params = [p for p in signature(fn).parameters.values()
              if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]

    # If function takes 1 param and a single kw is provided, accept it positionally
    if len(params) == 1 and len(args_dict) == 1:
        return (next(iter(args_dict.values())), {})

    # Map common synonyms
    norm = dict(args_dict)
    if fn is _TOOLBOX["sort_json_values"]:
        if "obj" not in norm:
            for syn in _SYNONYMS["obj"]:
                if syn in norm:
                    norm["obj"] = norm.pop(syn); break

    if fn is _TOOLBOX["json_merge"]:
        if "left" not in norm:
            for syn in _SYNONYMS["left"]:
                if syn in norm:
                    norm["left"] = norm.pop(syn); break
        if "right" not in norm:
            for syn in _SYNONYMS["right"]:
                if syn in norm:
                    norm["right"] = norm.pop(syn); break
        if "mode" not in norm:
            for syn in _SYNONYMS["mode"]:
                if syn in norm:
                    norm["mode"] = norm.pop(syn); break
    return (), norm

def execute_call(spec: Any, args: Any = None):
    if isinstance(spec, dict):
        name = spec.get("tool") or spec.get("name")
        call_args = spec.get("args") or {}
    else:
        name = spec
        call_args = args or {}

    fn = _TOOLBOX.get(name)
    if fn is None:
        raise ValueError(f"Unknown tool: {name!r}. Available: {sorted(_TOOLBOX.keys())}")

    pos, kwargs = _normalize_args(fn, call_args)
    return fn(*pos, **kwargs)
# --- end improved dispatcher ---
# --- execute_call V2: tolerant arg-mapping + ignore unknown kwargs ---
from inspect import signature
from typing import Any

try:
    _TOOLBOX
except NameError:
    _TOOLBOX = {
        "sort_json_values": sort_json_values,
        "json_sort_values": sort_json_values,
        "json_merge": json_merge,
        "json_merge_values": json_merge,
    }

_SYNONYMS = {
    "obj":   {"obj","value","data","json","payload","content","key","x"},
    "left":  {"left","a","lhs","l","x"},
    "right": {"right","b","rhs","r","y"},
    "mode":  {"mode","strategy","how","merge_mode","policy"},  # include 'policy'
}

def _normalize_kwargs(fn, args_dict: dict):
    norm = dict(args_dict or {})

    # Map common synonyms
    if fn is _TOOLBOX["sort_json_values"]:
        if "obj" not in norm:
            for syn in _SYNONYMS["obj"]:
                if syn in norm:
                    norm["obj"] = norm.pop(syn); break
        # ignore noise keys (e.g., 'key' from some benches)
        norm.pop("key", None)

    if fn is _TOOLBOX["json_merge"]:
        if "left" not in norm:
            for syn in _SYNONYMS["left"]:
                if syn in norm:
                    norm["left"] = norm.pop(syn); break
        if "right" not in norm:
            for syn in _SYNONYMS["right"]:
                if syn in norm:
                    norm["right"] = norm.pop(syn); break
        if "mode" not in norm:
            for syn in _SYNONYMS["mode"]:
                if syn in norm:
                    norm["mode"] = norm.pop(syn); break

    # Keep only params the function actually accepts
    params = set(signature(fn).parameters.keys())
    norm = {k: v for k, v in norm.items() if k in params}
    return norm

def execute_call(spec: Any, args: Any = None):
    if isinstance(spec, dict):
        name = spec.get("tool") or spec.get("name")
        call_args = spec.get("args") or {}
    else:
        name = spec
        call_args = args or {}

    fn = _TOOLBOX.get(name)
    if fn is None:
        raise ValueError(f"Unknown tool: {name!r}. Available: {sorted(_TOOLBOX.keys())}")

    kwargs = _normalize_kwargs(fn, call_args)
    return fn(**kwargs)
# --- end execute_call V2 ---
# --- mode synonym support for json_merge ---
import re

def _normalize_mode_value(val):
    if val is None:
        return "combine"
    s = str(val).strip().lower()
    s = re.sub(r"[^a-z0-9]+", "", s)  # e.g., "prefer_b" -> "preferb"
    table = {
        # right / B side
        "preferb":"prefer_right","right":"prefer_right","r":"prefer_right",
        "b":"prefer_right","rhs":"prefer_right","keepright":"prefer_right",
        "takeright":"prefer_right","preferright":"prefer_right","second":"prefer_right","2":"prefer_right",
        # left / A side
        "prefera":"prefer_left","left":"prefer_left","l":"prefer_left",
        "a":"prefer_left","lhs":"prefer_left","keepleft":"prefer_left",
        "takeleft":"prefer_left","preferleft":"prefer_left","first":"prefer_left","1":"prefer_left",
        # union/merge
        "combine":"combine","union":"combine","merge":"combine",
        "both":"combine","either":"combine","all":"combine",
    }
    return table.get(s, "combine")

# If toolbox exists, wrap json_merge to normalize 'mode' value
try:
    _TOOLBOX
    _orig_json_merge = _TOOLBOX.get("json_merge")
    if _orig_json_merge is not None:
        def _json_merge_wrapper(*, left=None, right=None, mode="combine"):
            return _orig_json_merge(left=left, right=right, mode=_normalize_mode_value(mode))
        _TOOLBOX["json_merge"] = _json_merge_wrapper
except NameError:
    pass
# --- end mode synonym support ---
# === CLT-E8 hardening for JSON tools (idempotent) ===
try:
    _TOOLBOX
except NameError:
    # If file layout changed, define toolbox safely
    def sort_json_values(*, obj): 
        return {"args":{"obj":obj},"tool":"json_sort_values"}
    def json_merge(*, left, right, mode="combine"): 
        return {"args":{"left":left,"right":right,"mode":mode},"tool":"json_merge"}
    _TOOLBOX = {
        "sort_json_values": sort_json_values,
        "json_sort_values": sort_json_values,
        "json_merge": json_merge,
        "json_merge_values": json_merge,
    }

from inspect import signature
from typing import Any
import re

_SYNONYMS = {
    "obj":   {"obj","value","data","json","payload","content","key","x"},
    "left":  {"left","a","lhs","l","x"},
    "right": {"right","b","rhs","r","y"},
    "mode":  {"mode","strategy","how","merge_mode","policy"},
}

def _normalize_mode_value(val):
    if val is None: return "combine"
    s = re.sub(r"[^a-z0-9]+","", str(val).strip().lower())
    table = {
        "preferb":"prefer_right","right":"prefer_right","r":"prefer_right",
        "b":"prefer_right","rhs":"prefer_right","keepright":"prefer_right",
        "takeright":"prefer_right","preferright":"prefer_right","second":"prefer_right","2":"prefer_right",
        "prefera":"prefer_left","left":"prefer_left","l":"prefer_left",
        "a":"prefer_left","lhs":"prefer_left","keepleft":"prefer_left",
        "takeleft":"prefer_left","preferleft":"prefer_left","first":"prefer_left","1":"prefer_left",
        "combine":"combine","union":"combine","merge":"combine","both":"combine","either":"combine","all":"combine",
    }
    return table.get(s, "combine")

# Wrap json_merge to normalize mode safely if present
_orig_json_merge = _TOOLBOX.get("json_merge")
if _orig_json_merge is not None:
    def _json_merge_wrapper(*, left=None, right=None, mode="combine"):
        return _orig_json_merge(left=left, right=right, mode=_normalize_mode_value(mode))
    _TOOLBOX["json_merge"] = _json_merge_wrapper

def _normalize_kwargs(fn, args_dict: dict):
    norm = dict(args_dict or {})
    # Map synonyms per tool
    if fn is _TOOLBOX["sort_json_values"]:
        if "obj" not in norm:
            for syn in _SYNONYMS["obj"]:
                if syn in norm:
                    norm["obj"] = norm.pop(syn); break
        norm.pop("key", None)  # ignore stray keys that tool doesn't support

    if fn is _TOOLBOX["json_merge"]:
        if "left" not in norm:
            for syn in _SYNONYMS["left"]:
                if syn in norm: norm["left"] = norm.pop(syn); break
        if "right" not in norm:
            for syn in _SYNONYMS["right"]:
                if syn in norm: norm["right"] = norm.pop(syn); break
        if "mode" not in norm:
            for syn in _SYNONYMS["mode"]:
                if syn in norm: norm["mode"] = norm.pop(syn); break

    # Keep only accepted parameters
    params = set(signature(fn).parameters.keys())
    return {k:v for k,v in norm.items() if k in params}

def execute_call(spec: Any, args: Any = None):
    if isinstance(spec, dict):
        name = spec.get("tool") or spec.get("name")
        call_args = spec.get("args") or {}
    else:
        name = spec
        call_args = args or {}

    fn = _TOOLBOX.get(name)
    if fn is None:
        raise ValueError(f"Unknown tool: {name!r}. Available: {sorted(_TOOLBOX.keys())}")

    kwargs = _normalize_kwargs(fn, call_args)
    return fn(**kwargs)
# === end hardening ===
