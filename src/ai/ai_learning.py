from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import json, re, time, os

# IO guard API
from src.io_guard import write_json, approved_targets

# ----------- Small helpers -----------

def _project_root() -> Path:
    roots = approved_targets()
    return Path(os.path.commonpath(roots)) if roots else Path.cwd()

def _load_json(path: Path) -> Optional[dict]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

def _latest_file(dir_: Path, pattern: str) -> Optional[Path]:
    cands = sorted(dir_.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return cands[0] if cands else None

# ----------- CLT-E8 Learning State -----------

@dataclass
class LearningState:
    # distilled facts from prior runs
    pass_rate: float
    determinism_ok: bool
    avg_latency_s: float
    failed_cases: List[str]
    notes: List[str]
    # targeted opportunities the planner can act on
    opportunities: List[Dict[str, Any]]

def _coherence_ratio_from_md(md_text: str) -> float:
    """
    Very light proxy: reward concise, consistent sections.
    0.0..1.0 where higher is 'more coherent' by simple structure signals.
    """
    if not md_text:
        return 0.2
    lines = [ln.strip() for ln in md_text.splitlines() if ln.strip()]
    if not lines:
        return 0.2
    # Structure score: headings, bullet discipline, and short lines
    heads = sum(1 for ln in lines if ln.startswith("#"))
    bullets = sum(1 for ln in lines if re.match(r"^[-*]\s", ln))
    long_lines = sum(1 for ln in lines if len(ln) > 120)
    n = len(lines)
    score = 0.3 + 0.2*(heads>0) + 0.2*(bullets>5) + 0.3*max(0, 1 - (long_lines / max(4, n)))
    return max(0.0, min(1.0, score))

def _extract_opportunities(summary: dict) -> List[Dict[str, Any]]:
    """
    Look for consistent failure themes we can fix with small, safe dispatch tweaks.
    """
    opps: List[Dict[str, Any]] = []
    results = (summary.get("summary") or {}).get("results") or []
    for r in results:
        if not isinstance(r, dict): 
            continue
        name = r.get("name","")
        ok = bool(r.get("ok"))
        out = (r.get("output") or "").lower()
        if ok:
            continue
        # Common tool-dispatch issues we saw (args aliasing or synonyms)
        if "unexpected keyword argument" in out or "unknown" in out or "policy" in out:
            opps.append({
                "kind": "tool_dispatch_arg_mapping",
                "test": name,
                "hint": "Normalize synonyms / ignore unknown kwargs in json_tools dispatcher.",
                "target_file": "src/tools/json_tools_v1.py",
            })
        # If determinism is bad per-test, we could add gating
        if "nondetermin" in out:
            opps.append({
                "kind": "determinism_gate",
                "test": name,
                "hint": "Clamp temperature / add post-check hashing.",
                "target_file": "bench/run_bench.py",
            })
    return opps

def load_learning_state(
    reports_dir: Optional[Path] = None,
    prefer_file: Optional[Path] = None,
    md_note: Optional[Path] = None,
) -> LearningState:
    root = _project_root()
    reports = reports_dir or (root / "reports")

    summary_json: Optional[dict] = None
    if prefer_file and prefer_file.exists():
        summary_json = _load_json(prefer_file)
    if summary_json is None:
        latest = _latest_file(reports, "bench_*.json")
        if latest:
            summary_json = _load_json(latest)
    if summary_json is None:
        # Minimal empty state
        return LearningState(
            pass_rate=0.0, determinism_ok=False, avg_latency_s=0.0,
            failed_cases=[], notes=["No report JSON found."], opportunities=[]
        )

    sumroot = summary_json.get("summary") or {}
    passed = int(((sumroot.get("success") or {}).get("passed") or 0))
    total = int(((sumroot.get("success") or {}).get("total") or 0))
    pass_rate = (passed / total) if total else 0.0
    determinism_ok = bool(sumroot.get("determinism_ok", False))
    avg_latency = float(((sumroot.get("latency") or {}).get("avg_s") or 0.0))

    failed_cases: List[str] = []
    for r in (sumroot.get("results") or []):
        if not r.get("ok"):
            failed_cases.append(str(r.get("name")))

    # Optional MD coherence sniff
    coherence = 0.5
    if md_note and md_note.exists():
        coherence = _coherence_ratio_from_md(md_note.read_text(encoding="utf-8"))
    else:
        # try to infer md sibling for the latest json
        if prefer_file:
            md_candidate = prefer_file.with_suffix(".md")
            if md_candidate.exists():
                coherence = _coherence_ratio_from_md(md_candidate.read_text(encoding="utf-8"))
        else:
            latest_md = _latest_file(reports, "bench_*.md")
            if latest_md:
                coherence = _coherence_ratio_from_md(latest_md.read_text(encoding="utf-8"))

    notes = [
        f"pass_rate={pass_rate:.3f}",
        f"determinism_ok={determinism_ok}",
        f"avg_latency_s={avg_latency:.3f}",
        f"coherence~={coherence:.2f}",
    ]
    opps = _extract_opportunities(summary_json)
    return LearningState(
        pass_rate=pass_rate,
        determinism_ok=determinism_ok,
        avg_latency_s=avg_latency,
        failed_cases=failed_cases,
        notes=notes,
        opportunities=opps,
    )
