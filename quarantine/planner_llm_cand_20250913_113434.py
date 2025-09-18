# FILE: src/llm/planner_llm.py
"""
planner_llm.py — Plan suggestion with LLM-optional fallback

Shape contract (for tests and downstream code):
Return a list of step objects, each with keys:
  - action: str
  - args: dict
  - explain: str   (human-readable, stable offline)

If LLM is enabled, we ask it for a plan (JSON with the above keys).
If LLM is disabled (default for tests) or errors out, we return a deterministic fallback
that handles simple "Compute X + Y ... verify ..." tasks.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from src.ai_runtime import chat, llm_enabled

_STEP_SHAPE = {"action": str, "args": dict, "explain": str}


def _fallback_parse_addition(task: str) -> Dict[str, int] | None:
    """
    Minimal regex to support tasks like:
      "Compute 21 + 21 using available tools, verify, and record the method."
      "Compute 34 + 55 ..."
    Returns {'a': int, 'b': int} or None.
    """
    m = re.search(r"compute\s+(-?\d+)\s*\+\s*(-?\d+)", task, flags=re.I)
    if not m:
        return None
    a, b = int(m.group(1)), int(m.group(2))
    return {"a": a, "b": b}


def _ensure_shape(steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for s in steps:
        action = str(s.get("action", "noop"))
        args = s.get("args", {})
        explain = str(s.get("explain", ""))
        out.append({"action": action, "args": dict(args), "explain": explain})
    return out


def suggest_plan(task: str, *, temperature: float = 0.0) -> List[Dict[str, Any]]:
    """
    Return a list of {action,args,explain} steps.
    Offline default is deterministic and requires no network.
    """
    # Offline deterministic path (default)
    if not llm_enabled():
        add = _fallback_parse_addition(task)
        if add is not None:
            a, b = add["a"], add["b"]
            return _ensure_shape(
                [
                    {
                        "action": "semantic_recall",
                        "args": {"query": task},
                        "explain": "Check memory for prior identical computation.",
                    },
                    {
                        "action": "plan_compute",
                        "args": {"op": "add", "a": a, "b": b},
                        "explain": "Plan: use arithmetic tool to add a+b.",
                    },
                    {
                        "action": "tool_add",
                        "args": {"a": a, "b": b},
                        "explain": "Deterministic addition using built-in tool.",
                    },
                    {
                        "action": "critic_check",
                        "args": {"equals": a + b},
                        "explain": "Verify result equals expected.",
                    },
                    {
                        "action": "record_episode",
                        "args": {"success": True},
                        "explain": "Record method and outcome to episodic memory.",
                    },
                ]
            )
        # Generic conservative fallback
        return _ensure_shape(
            [
                {
                    "action": "semantic_recall",
                    "args": {"query": task},
                    "explain": "Retrieve related prior tasks.",
                },
                {
                    "action": "plan_simple",
                    "args": {"strategy": "decompose_and_act"},
                    "explain": "Decompose into simple, verifiable substeps.",
                },
                {
                    "action": "record_episode",
                    "args": {"success": False, "note": "No specific offline tool path found."},
                    "explain": "Log for future improvement.",
                },
            ]
        )

    # LLM-enabled path — ask for explicit JSON steps
    try:
        sys = (
            "You are a planning module. Output ONLY a JSON array of steps. "
            "Each step is an object with keys: action (string), args (object), explain (string). "
            "No prose outside JSON."
        )
        prompt = (
            f"Produce a small, deterministic plan to accomplish:\n{task}\n"
            "Keep steps minimal and explain briefly. Use 'tool_add' for additions."
        )
        raw = chat(
            [{"role": "system", "content": sys}, {"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=320,
        )
        txt = raw.strip()
        if txt.startswith("```"):
            txt = txt.strip("` \n")
            if txt.lower().startswith("json"):
                txt = txt[4:].lstrip()
        steps = json.loads(txt)
        if not isinstance(steps, list):
            raise ValueError("Planner output is not a JSON array")
        return _ensure_shape(steps)
    except Exception:
        # Safe fallback if LLM/network hiccups
        return _ensure_shape(
            [
                {
                    "action": "semantic_recall",
                    "args": {"query": task},
                    "explain": "Fallback after LLM error.",
                },
                {
                    "action": "plan_simple",
                    "args": {"strategy": "decompose_and_act"},
                    "explain": "Deterministic rescue path.",
                },
                {
                    "action": "record_episode",
                    "args": {"success": False, "note": "LLM error; used fallback."},
                    "explain": "Log for audit.",
                },
            ]
        )