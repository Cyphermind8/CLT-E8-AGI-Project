# FILE: src/analyze_runs.py
from __future__ import annotations
from pathlib import Path
import json, os, re, time
from typing import Any, Dict, List

from src.io_guard import write_json, approved_targets

def _project_root() -> Path:
    roots = approved_targets()
    return Path(os.path.commonpath(roots)) if roots else Path.cwd()

def _anchor(p: str | Path) -> Path:
    p = Path(p)
    return p if p.is_absolute() else _project_root() / p

def _latest_run_dir() -> Path | None:
    runs = _anchor("runs")
    if not runs.exists():
        return None
    candidates = [d for d in runs.iterdir() if d.is_dir() and re.match(r"run_\\d{8}_\\d{6}$", d.name)]
    if not candidates:
        return None
    return sorted(candidates, key=lambda d: d.stat().st_mtime, reverse=True)[0]

def analyze_latest() -> Dict[str, Any]:
    rd = _latest_run_dir()
    if rd is None:
        return {"ok": False, "reason": "no runs directory or no run_* folders found"}

    out: Dict[str, Any] = {"ok": True, "run_dir": str(rd), "files": {}, "summary": {}}

    # best-effort read of common artifacts
    for name in ("summary.json", "run_meta.json"):
        p = Path(rd) / name
        if p.exists():
            try:
                out["files"][name] = json.loads(p.read_text(encoding="utf-8"))
            except Exception as e:
                out["files"][name] = {"error": f"read_failed: {e!r}"}

    # tiny derived summary
    s = out["files"].get("summary.json") or {}
    out["summary"] = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "ok": bool(s.get("ok", True)),
        "keys": sorted(list(s.keys())),
    }
    return out

if __name__ == "__main__":
    # Governor-safe write to data/reports (usually approved)
    report = analyze_latest()
    write_json(str(_anchor("data/reports/analysis_latest.json")), report)
