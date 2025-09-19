from __future__ import annotations
import os, sys, time, subprocess
from pathlib import Path
from typing import Dict, Any

from src.io_guard import write_json, approved_targets

def _project_root() -> Path:
    roots = approved_targets()
    return Path(os.path.commonpath(roots)) if roots else Path.cwd()

def _anchor(p: str | Path) -> Path:
    p = Path(p)
    return p if p.is_absolute() else _project_root() / p

def _run(cmd: list[str], cwd: Path) -> Dict[str, Any]:
    t0 = time.time()
    try:
        r = subprocess.run(cmd, cwd=str(cwd), check=True, capture_output=True, text=True)
        ok = True
        out = r.stdout
        err = r.stderr
        code = 0
    except subprocess.CalledProcessError as e:
        ok = False
        out = e.stdout or ""
        err = e.stderr or str(e)
        code = e.returncode
    dt = time.time() - t0
    return {"ok": ok, "code": code, "latency_s": round(dt, 3), "stdout": out, "stderr": err}

def main():
    root = _project_root()
    # One cycle: bench → analyze → (optional) coherence step runner
    results: Dict[str, Any] = {"ts": time.time(), "steps": []}

    # 1) Bench (uses your existing scripts/run_bench_with_log.py)
    results["steps"].append({
        "name": "bench",
        **_run([sys.executable, str(_anchor("scripts/run_bench_with_log.py"))], cwd=root)
    })

    # 2) Analyze runs (writes reports/analysis_latest.json internally)
    results["steps"].append({
        "name": "analyze_runs",
        **_run([sys.executable, str(_anchor("scripts/analyze_runs.py"))], cwd=root)
    })

    # 3) Coherence cycle (tonight’s self-improvement attempt)
    results["steps"].append({
        "name": "coherence_cycle",
        **_run([sys.executable, str(_anchor("scripts/run_coherence_cycle.py"))], cwd=root)
    })

    # Governor-safe summary of the orchestrator
    write_json(str(_anchor("logs/auto_clt_loop_last.json")), results)

if __name__ == "__main__":
    main()
