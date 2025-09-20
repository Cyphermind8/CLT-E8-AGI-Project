# FILE: src/tools/json_tools_v1.py
# UTF-8 (no BOM) — deterministic, stdlib-only helpers for JSON ops.

from __future__ import annotations
from typing import Any, Dict, List, Iterable
from inspect import signature
import json
import re
import copy

__all__ = [
    "sort_json_values",        # recursive; sorts lists and orders dict keys alphabetically
    "json_sort_values",        # legacy alias: optional key to sort a single field
    "json_merge",              # combine / prefer_left / prefer_right
    "execute_call",            # tolerant dispatcher
]

# -----------------------------
# Small helpers
# -----------------------------

def _deepcopy_json(obj: Any) -> Any:
    """Safe deep copy for JSON-like objects."""
    return copy.deepcopy(obj)

def _try_sort_list(lst: list) -> list:
    """Sort if elements are mutually comparable; otherwise keep original order."""
    try:
        return sorted(lst)
    except TypeError:
        return list(lst)

def _normalize_mode_value(val: Any) -> str:
    """
    Normalize merge policy to one of: 'combine', 'prefer_left', 'prefer_right'.
    Accepts direct values and a wide set of synonyms.
    """
    if val is None:
        return "combine"
    s_raw = str(val).strip()
    # Accept canonical strings as-is
    if s_raw in {"combine", "prefer_left", "prefer_right"}:
        return s_raw
    # Normalize noisy variants
    s = re.sub(r"[^a-z0-9]+", "", s_raw.lower())
    table = {
        # prefer right
        "preferright": "prefer_right", "right": "prefer_right", "r": "prefer_right",
        "b": "prefer_right", "rhs": "prefer_right", "2": "prefer_right",
        # prefer left
        "preferleft": "prefer_left", "left": "prefer_left", "l": "prefer_left",
        "a": "prefer_left", "lhs": "prefer_left", "1": "prefer_left",
        # combine/union
        "combine": "combine", "union": "combine", "merge": "combine",
        "both": "combine", "either": "combine", "all": "combine",
        # fallbacks
        "": "combine",
    }
    return table.get(s, "combine")

def _unique_preserve_order(seq: Iterable[Any]) -> List[Any]:
    """Return a list with first-occurrence order preserved (by JSON-serialized identity)."""
    seen = set()
    out: List[Any] = []
    for x in seq:
        k = json.dumps(x, sort_keys=True, ensure_ascii=False)
        if k in seen:
            continue
        seen.add(k)
        out.append(x)
    return out

# -----------------------------
# Public API
# -----------------------------

def sort_json_values(obj: Any) -> Any:
    """
    Recursively traverse a JSON-like structure:
      - Sort any lists encountered (if elements are comparable).
      - Return dicts with **keys in alphabetical order** (values processed recursively).
    Scalars are returned unchanged.
    """
    if isinstance(obj, list):
        rec = [sort_json_values(v) for v in obj]
        return _try_sort_list(rec)
    if isinstance(obj, dict):
        # Recurse into values and rebuild dict with sorted keys
        keys = sorted(obj.keys())
        out: Dict[str, Any] = {}
        for k in keys:
            out[k] = sort_json_values(obj[k])
        return out
    return _deepcopy_json(obj)

def json_sort_values(obj: Dict[str, Any], key: str | None = None) -> Dict[str, Any]:
    """
    Back-compat alias:
      - If key is provided: only sort obj[key] when it is a list (non-destructive to other fields).
      - If key is None: behave like recursive sort_json_values(obj).
    """
    if key is None:
      return sort_json_values(obj)
    result = _deepcopy_json(obj)
    if isinstance(result, dict) and key in result and isinstance(result[key], list):
        result[key] = _try_sort_list(result[key])
    return result

def json_merge(left: Any, right: Any, mode: str | None = "combine") -> Any:
    """
    Merge two JSON-like structures with one of three policies:

    - combine (default):
        * dict: recursive combine by key
        * list: union with first-occurrence order
        * scalar mismatch: choose right if not None, else left
    - prefer_left:
        * dict/list/scalar: choose left if present, else right
    - prefer_right:
        * dict/list/scalar: choose right if present, else left
    """
    policy = _normalize_mode_value(mode)

    if policy == "prefer_left":
        return _deepcopy_json(left) if left is not None else _deepcopy_json(right)
    if policy == "prefer_right":
        return _deepcopy_json(right) if right is not None else _deepcopy_json(left)

    # combine policy
    if isinstance(left, dict) and isinstance(right, dict):
        out: Dict[str, Any] = {}
        keys = set(left.keys()) | set(right.keys())
        for k in keys:
            if k in left and k in right:
                out[k] = json_merge(left[k], right[k], mode="combine")
            elif k in left:
                out[k] = _deepcopy_json(left[k])
            else:
                out[k] = _deepcopy_json(right[k])
        return out

    if isinstance(left, list) and isinstance(right, list):
        return _unique_preserve_order([*_deepcopy_json(left), *_deepcopy_json(right)])

    # Mismatched or scalar types under "combine": prefer the more defined value.
    return _deepcopy_json(right) if right is not None else _deepcopy_json(left)

# -----------------------------
# Minimal tool dispatcher (tolerant)
# -----------------------------

_TOOLBOX = {
    "sort_json_values": sort_json_values,
    "json_sort_values": json_sort_values,
    "json_merge": json_merge,
}

# Loose synonyms for kwargs we’ve seen in the wild.
_SYN_KW = {
    "obj":   {"obj", "value", "data", "json", "payload", "content"},
    "left":  {"left", "a", "lhs", "l", "x"},
    "right": {"right", "b", "rhs", "r", "y"},
    "mode":  {"mode", "strategy", "how", "merge_mode", "policy"},
    "key":   {"key", "path", "field", "name"},
}

def _normalize_kwargs(fn, args_dict: dict) -> dict:
    """Map common synonym keys to the function’s real parameters and drop unknowns."""
    norm = dict(args_dict or {})
    params = set(signature(fn).parameters.keys())

    def _fill(canon: str):
        if canon in params and canon not in norm:
            for syn in _SYN_KW[canon]:
                if syn in norm:
                    norm[canon] = norm.pop(syn)
                    break

    _fill("obj")
    _fill("left")
    _fill("right")
    _fill("mode")
    _fill("key")

    # Drop unknown kwargs (tolerant)
    return {k: v for k, v in norm.items() if k in params}

def execute_call(spec: Any, args: Any = None) -> Any:
    """
    Uniform entrypoint:
      execute_call("json_merge", {"left": {...}, "right": {...}, "mode": "combine"})
      execute_call({"tool": "sort_json_values", "args": {"obj": {...}}})
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

    kwargs = _normalize_kwargs(fn, call_args)
    if "mode" in kwargs:
        kwargs["mode"] = _normalize_mode_value(kwargs["mode"])
    return fn(**kwargs)

# -----------------------------
# CLI smoke (optional)
# -----------------------------

def _print_json(x: Any) -> None:
    print(json.dumps(x, ensure_ascii=False, sort_keys=True))

if __name__ == "__main__":
    import sys
    argv = sys.argv[1:]
    if not argv:
        sys.exit(0)
    try:
        if len(argv) == 1:
            obj = json.loads(argv[0])
            _print_json(sort_json_values(obj))
        else:
            left = json.loads(argv[0]); right = json.loads(argv[1])
            mode = argv[2] if len(argv) > 2 else "combine"
            _print_json(json_merge(left, right, mode=mode))
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(2)
