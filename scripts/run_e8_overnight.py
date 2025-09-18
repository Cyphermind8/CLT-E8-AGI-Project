from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List
import os, time, json

from src.io_guard import write_json, approved_targets
from src.utils.runlog import start_run, finish_run
from src.clt_e8.bench_api import run_bench
from src.clt_e8.scorecard import compare
from src.clt_e8.shadow import materialize
from src.clt_e8.passes import json_tools

def _project_root() -> Path:
    roots = approved_targets()
    return Path(os.path.commonpath(roots)) if roots else Path.cwd()

def cycle_once(meta: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    1) Run baseline bench on real workspace (read-only).
    2) Create shadow workspace under runs/<rid>/ws.
    3) Apply E8 passes to the shadow (idempotent).
    4) Run bench in shadow.
    5) Compare and emit an E8 report into runs/<rid>/e8_report.json.
    """
    meta = dict(meta or {})
    root = _project_root()
    rid_dir = start_run({**meta, "phase": "e8_cycle"})
    try:
        # Baseline
        base_summary, base_json = run_bench(cwd=str(root), project_root=str(root))

        # Shadow materialization
        ws_root = rid_dir / "ws"
        ws_root.mkdir(parents=True, exist_ok=True)
        materialize(root, ws_root)

        # Passes
        changes: List[str] = []
        changes += json_tools.apply(ws_root)

        # Candidate bench (ensure Governor points at ws_root)
        cand_summary, cand_json = run_bench(cwd=str(ws_root), project_root=str(ws_root))

        verdict = compare(base_summary, cand_summary)
        report = {
            "rid": rid_dir.name,
            "timestamp": time.time(),
            "baseline": {"summary": base_summary, "json": base_json},
            "candidate": {"summary": cand_summary, "json": cand_json},
            "changes": changes,
            "verdict": {
                "is_better": verdict.is_better,
                "reason": verdict.reason,
                "delta_passed": verdict.delta_passed,
                "rel_latency_impr": verdict.rel_latency_impr,
                "determinism_ok": verdict.determinism_ok,
            },
        }
        write_json(str(rid_dir / "e8_report.json"), report)
        return report
    finally:
        finish_run(rid_dir, {"ok": True})