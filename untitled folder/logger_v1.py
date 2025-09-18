"""
logger_v1.py — JSON logger for experiment runs (schema v1 compatible).

Writes a single JSON per run with setup info, per-attempt records, and headline metrics.
Computes GC (grounded correctness) and CSC (coherence-success correlation) automatically.
"""
import json, math
from datetime import datetime
from typing import Dict, Any, List

class RunLogger:
    def __init__(self, run_id: str, base_dir: str = ".", config: Dict[str, Any] = None,
                 dataset: str = "MathCode", hardware: Dict[str, Any] = None, notes: str = ""):
        self.data = {
            "run_id": run_id,
            "date": datetime.utcnow().date().isoformat(),
            "setup": {
                "code_version": "mvp-v1",
                "config": config or {},
                "seeds": {"global": 42},
                "dataset": dataset,
                "hardware": hardware or {},
                "notes": notes
            },
            "metrics": {
                "GC": {"passed": 0, "total": 0, "pct": 0.0},
                "GfD": {"passed": 0, "total": 0, "pct": 0.0},
                "MU": {"delta_accuracy": 0.0, "delta_latency": 0.0},
                "CH": {"resolved": 0, "injected": 0, "pct": 0.0},
                "SRE": {"recovered": 0, "failures": 0, "pct": 0.0},
                "CSC": {"r": 0.0, "p": 1.0}
            },
            "ablation": {},
            "attempts": [],
            "artifacts": {"plots": [], "logs_path": "", "config_snapshot_path": ""}
        }
        self.base_dir = base_dir

    def record_attempt(self, task_id: str, hypothesis_id: str, mode: str,
                       coherence: Dict[str, float], retrieval: Dict[str, Any] = None,
                       contradictions: int = 0, passed: bool = False, error: str = "",
                       timing_ms: float = 0.0, slipstate_ids: List[str] = None) -> None:
        self.data["attempts"].append({
            "task_id": task_id,
            "hypothesis_id": hypothesis_id,
            "mode": mode,
            "coherence": {
                "d_entropy": float(coherence.get("d_entropy", 0.0)),
                "consistency": float(coherence.get("consistency", 0.0)),
                "contradictions": float(coherence.get("contradictions", 0.0)),
                "total": float(coherence.get("total", 0.0))
            },
            "retrieval": retrieval or {},
            "contradictions": int(contradictions),
            "pass": bool(passed),
            "error": error or "",
            "timing_ms": float(timing_ms),
            "slipstate_ids": slipstate_ids or []
        })

    def finalize_metrics(self) -> None:
        # GC
        total = len(self.data["attempts"])
        passed = sum(1 for a in self.data["attempts"] if a["pass"])
        self.data["metrics"]["GC"] = {"passed": passed, "total": total, "pct": (100.0 * passed / max(1, total))}

        # CSC (Pearson r) between coherence.total and pass (0/1), with rough p-value approximation
        xs = [a["coherence"]["total"] for a in self.data["attempts"]]
        ys = [1.0 if a["pass"] else 0.0 for a in self.data["attempts"]]
        n = len(xs)
        if n >= 3:
            meanx = sum(xs) / n
            meany = sum(ys) / n
            cov = sum((x - meanx) * (y - meany) for x, y in zip(xs, ys))
            varx = sum((x - meanx) ** 2 for x in xs)
            vary = sum((y - meany) ** 2 for y in ys)
            r = cov / (math.sqrt(varx * max(vary, 1e-9)) + 1e-9)
            # t-stat approximation and very rough p-value surrogate
            t = r * math.sqrt(max(n - 2, 1) / max(1 - r * r, 1e-9))
            p = math.exp(-abs(t))
            self.data["metrics"]["CSC"] = {"r": float(r), "p": float(p)}

    def write(self, path: str) -> None:
        self.finalize_metrics()
        self.data["artifacts"]["logs_path"] = path
        with open(path, "w") as f:
            json.dump(self.data, f, indent=2)
