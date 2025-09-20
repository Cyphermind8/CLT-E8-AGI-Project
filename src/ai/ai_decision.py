from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from pathlib import Path
import time, textwrap, json, os

from src.io_guard import write_json, append_text, approved_targets

def _project_root() -> Path:
    roots = approved_targets()
    return Path(os.path.commonpath(roots)) if roots else Path.cwd()

@dataclass
class Plan:
    rid: str
    rationale: List[str]
    actions: List[Dict[str, Any]]  # each action is a proposed patch or task

def _rid() -> str:
    return time.strftime("run_%Y%m%d_%H%M%S")

def _score_opportunity(kind: str, pass_rate: float, determinism_ok: bool) -> float:
    # Simple priority: fix correctness > determinism > latency.
    base = {
        "tool_dispatch_arg_mapping": 1.0,
        "mode_synonym_normalizer": 0.9,
        "determinism_gate": 0.8,
        "latency_tuning": 0.7,
    }.get(kind, 0.5)
    # If determinism is already ok, lower determinism-related urgency
    if determinism_ok and kind == "determinism_gate":
        base -= 0.2
    # boost if pass rate is below 100%
    if pass_rate < 1.0 and kind in ("tool_dispatch_arg_mapping","mode_synonym_normalizer"):
        base += 0.2
    return max(0.0, min(1.2, base))

def _patch_snippet(kind: str) -> str:
    """
    Concrete, copy-pastable patch snippets (text-only) we learned helped before.
    They are suggestions; we don't auto-apply yet.
    """
    if kind == "tool_dispatch_arg_mapping":
        return textwrap.dedent("""\
        # --- execute_call V2: tolerant arg-mapping + ignore unknown kwargs ---
        # (Paste into src/tools/json_tools_v1.py near the dispatcher.)
        from inspect import signature
        from typing import Any
        try:
            _TOOLBOX
        except NameError:
            _TOOLBOX = {}
        _SYNONYMS = {
            "obj":   {"obj","value","data","json","payload","content","key","x"},
            "left":  {"left","a","lhs","l","x"},
            "right": {"right","b","rhs","r","y"},
            "mode":  {"mode","strategy","how","merge_mode","policy"},
        }
        def _normalize_kwargs(fn, args_dict: dict):
            norm = dict(args_dict or {})
            if "obj" not in norm:
                for syn in _SYNONYMS["obj"]:
                    if syn in norm: norm["obj"] = norm.pop(syn); break
            # ignore irrelevant
            norm.pop("key", None)
            params = set(signature(fn).parameters.keys())
            return {k:v for k,v in norm.items() if k in params}
        def execute_call(spec: Any, args: Any = None):
            if isinstance(spec, dict):
                name = spec.get("tool") or spec.get("name")
                call_args = spec.get("args") or {}
            else:
                name = spec; call_args = args or {}
            fn = _TOOLBOX.get(name)
            if fn is None:
                raise ValueError(f"Unknown tool: {name!r}. Available: {sorted(_TOOLBOX.keys())}")
            kwargs = _normalize_kwargs(fn, call_args)
            return fn(**kwargs)
        # --- end execute_call V2 ---
        """)
    if kind == "mode_synonym_normalizer":
        return textwrap.dedent("""\
        # --- mode synonym support for json_merge ---
        import re
        def _normalize_mode_value(val):
            if val is None: return "combine"
            s = re.sub(r"[^a-z0-9]+","", str(val).strip().lower())
            table = {
                "preferb":"prefer_right","right":"prefer_right","r":"prefer_right","b":"prefer_right","rhs":"prefer_right","2":"prefer_right",
                "prefera":"prefer_left","left":"prefer_left","l":"prefer_left","a":"prefer_left","lhs":"prefer_left","1":"prefer_left",
                "combine":"combine","union":"combine","merge":"combine","both":"combine","either":"combine","all":"combine",
            }
            return table.get(s, "combine")
        try:
            _TOOLBOX
            _orig = _TOOLBOX.get("json_merge")
            if _orig:
                def _json_merge_wrapper(*, left=None, right=None, mode="combine"):
                    return _orig(left=left, right=right, mode=_normalize_mode_value(mode))
                _TOOLBOX["json_merge"] = _json_merge_wrapper
        except NameError:
            pass
        # --- end mode synonym support ---
        """)
    if kind == "determinism_gate":
        return textwrap.dedent("""\
        # Determinism gate (example): before reporting success, hash the output of each test
        # and fail if hash swings across repeated runs. See bench/run_bench.py -> det hash logic.
        # Ensure temperature=0 and seed fixed.
        """)
    if kind == "latency_tuning":
        return "# Latency tuning: increase n_batch or enable KV cache reuse hints safely."
    return "# (no snippet)"

def make_plan(learning_state: Any) -> Plan:
    rid = _rid()
    reasons = [
        "CLT-E8 gate: prefer high-precision, low-divergence edits.",
        f"Signals: {', '.join(learning_state.notes)}",
        "Priority: fix systematic dispatch/keying errors before experimentation.",
    ]
    actions: List[Dict[str, Any]] = []

    # Rank opportunities and produce patch suggestions
    ranked = sorted(
        learning_state.opportunities,
        key=lambda o: _score_opportunity(o.get("kind",""), learning_state.pass_rate, learning_state.determinism_ok),
        reverse=True,
    )

    # De-duplicate by kind + target
    seen = set()
    for o in ranked:
        sig = (o.get("kind"), o.get("target_file"))
        if sig in seen: 
            continue
        seen.add(sig)
        actions.append({
            "type": "suggest_patch",
            "target_file": o.get("target_file"),
            "kind": o.get("kind"),
            "test": o.get("test"),
            "snippet": _patch_snippet(o.get("kind")),
        })

    # Always add a “run again” action under same harness to verify determinism
    actions.append({
        "type": "rerun_bench",
        "args": {"determinism_runs": 2}
    })

    return Plan(rid=rid, rationale=reasons, actions=actions)

def write_plan(plan: Plan, out_dir: Optional[Path] = None) -> Path:
    root = _project_root()
    run_dir = (out_dir or (root / "runs" / plan.rid))
    run_dir.mkdir(parents=True, exist_ok=True)

    # Save as json + markdown (both via guard)
    plan_json = {
        "rid": plan.rid,
        "rationale": plan.rationale,
        "actions": plan.actions,
        "ts": time.time(),
    }
    write_json(str(run_dir / "coherence_plan.json"), plan_json)

    md_lines = ["# Coherence Plan", f"- rid: `{plan.rid}`", ""]
    md_lines += [f"- {r}" for r in plan.rationale]
    md_lines.append("")
    for i, act in enumerate(plan.actions, 1):
        md_lines.append(f"## Action {i}: {act.get('type')}")
        if act.get("target_file"):
            md_lines.append(f"- target: `{act['target_file']}`")
        if act.get("kind"):
            md_lines.append(f"- kind: `{act['kind']}`")
        if act.get("test"):
            md_lines.append(f"- failing test: `{act['test']}`")
        snip = act.get("snippet") or ""
        if snip.strip():
            md_lines.append("\n```python")
            md_lines.append(snip.strip())
            md_lines.append("```\n")

    append_text(str(run_dir / "coherence_plan.md"), "\n".join(md_lines) + "\n")
    return run_dir
