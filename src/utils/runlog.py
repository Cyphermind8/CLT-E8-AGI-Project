from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, Union
import time, os

# use the same root the Governor/io_guard uses
from src.io_guard import write_json, approved_targets

def _project_root() -> Path:
    roots = approved_targets()  # e.g., C:\AI_Project\data, ...\logs, ...
    if not roots:
        return Path.cwd()
    return Path(os.path.commonpath(roots))

def _anchor(p: Union[str, Path]) -> Path:
    p = Path(p)
    return p if p.is_absolute() else _project_root() / p

def start_run(meta: Dict[str, Any]) -> Path:
    rid = time.strftime("run_%Y%m%d_%H%M%S")
    run_dir = _anchor(Path("runs") / rid)
    # writing JSON will create the parent dir via Governor.ensure_parent
    write_json(str(run_dir / "run_meta.json"), {**meta, "rid": rid, "ts": time.time()})
    return run_dir

def finish_run(run_dir: Union[str, Path], summary: Dict[str, Any]) -> None:
    run_dir = _anchor(run_dir)
    write_json(str(run_dir / "summary.json"), {**summary, "finished_ts": time.time()})
