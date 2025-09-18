# FILE: src/tools/json_tools_v1.py
"""
Deterministic JSON tools for bench tasks and future planners.

Tools:
- json_sort_values: sort the list at a given key (stable, numeric-first).
- json_merge: merge two dicts with an explicit conflict policy.

All functions are pure and side-effect free.
"""

from __future__ import annotations
from typing import Any, Dict, List
import json

JsonObj = Dict[str, Any]

def _stable_sort_list(v: List[Any]) -> List[Any]:
    """
    Sort with deterministic behavior across types:
    - If all items are numbers -> numeric sort.
    - Else -> stringified sort.
    """
    if all(isinstance(x, (int, float)) for x in v):
        return sorted(v)
    return sorted(v, key=lambda x: json.dumps(x, separators=(",", ":"), ensure_ascii=False))

def json_sort_values(obj: JsonObj, key: str) -> JsonObj:
    """
    Return a copy of obj with obj[key] sorted.
    Raises ValueError if key missing or not a list.
    """
    if key not in obj:
        raise ValueError(f"key '{key}' not found")
    v = obj[key]
    if not isinstance(v, list):
        raise ValueError(f"key '{key}' must be a list")
    return {**obj, key: _stable_sort_list(v)}

def json_merge(a: JsonObj, b: JsonObj, policy: str = "prefer_b") -> JsonObj:
    """
    Merge two dicts with explicit policy on conflicts:
      - prefer_b: B overwrites A when keys collide and values differ
      - prefer_a: A keeps its value on collision
      - error:    raise ValueError on collision
    Default is 'prefer_b' to match our bench expectation.
    """
    out = dict(a)
    for k, v in b.items():
        if k in out and out[k] != v:
            if policy == "prefer_a":
                continue
            if policy == "error":
                raise ValueError(f"conflict at key '{k}'")
            # prefer_b
            out[k] = v
        else:
            out[k] = v
    return out

def execute_call(call: JsonObj) -> Any:
    """
    Execute a local 'tool call' described as:
        {"tool":"json_sort_values","args":{"obj":{...},"key":"x"}}
    or  {"tool":"json_merge","args":{"a":{...},"b":{...},"policy":"prefer_b"}}
    """
    if not isinstance(call, dict):
        raise ValueError("tool call must be a dict")
    tool = call.get("tool")
    args = call.get("args") or {}
    if tool == "json_sort_values":
        return json_sort_values(args["obj"], args["key"])
    if tool == "json_merge":
        return json_merge(args["a"], args["b"], args.get("policy", "prefer_b"))
    raise ValueError(f"unknown tool '{tool}'")
