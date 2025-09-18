# FILE: src/utils/perflog.py
from __future__ import annotations
import json, os, tempfile
from pathlib import Path
from typing import Any, Dict

def _atomic_write_json(path: Path, payload: Dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmpname = tempfile.mkstemp(prefix="perf_", suffix=".json", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        os.replace(tmpname, path)
    except Exception:
        try:
            os.remove(tmpname)
        except Exception:
            pass
        raise

def append_performance(log_path: Path, entry: Dict[str, Any]) -> None:
    log_path = Path(log_path)
    if log_path.exists():
        try:
            data = json.loads(log_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or "runs" not in data:
                data = {"runs": []}
        except Exception:
            data = {"runs": []}
    else:
        data = {"runs": []}
    data["runs"].append(entry)
    _atomic_write_json(log_path, data)
