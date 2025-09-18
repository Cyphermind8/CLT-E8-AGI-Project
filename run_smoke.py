# FILE: run_smoke.py
import os, json, time
from pathlib import Path

from src.workspace_v1 import Workspace
from src.memory.episodic_v1 import EpisodicMemory
from src.memory.semantic_v1 import SemanticMemory
from src.memory.procedural_v1 import ProceduralMemory
from src.utils.perflog import append_performance

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
(DATA_DIR / "episodic.jsonl").touch(exist_ok=True)
(DATA_DIR / "semantic.jsonl").touch(exist_ok=True)
(DATA_DIR / "procedural.jsonl").touch(exist_ok=True)

PERF_LOG = Path("ai_performance_log.json")

def log_report(report_path: Path, payload: dict):
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

def main():
    ws = Workspace()  # sense-plan-act-verify-reflect
    episodic = EpisodicMemory(DATA_DIR / "episodic.jsonl")
    semantic = SemanticMemory(DATA_DIR / "semantic.jsonl")
    procedural = ProceduralMemory(DATA_DIR / "procedural.jsonl")

    task = "Compute 21 + 21 using available tools, verify, and record the method."

    run1 = ws.run(task, episodic=episodic, semantic=semantic, procedural=procedural)
    run2 = ws.run(task, episodic=episodic, semantic=semantic, procedural=procedural)

    report = {
        "task": task,
        "run1": run1,
        "run2": run2,
        "improvement": {
            "steps_delta": (run1.get("steps", 0) - run2.get("steps", 0)),
            "latency_delta_ms": max(0, run1.get("latency_ms", 0) - run2.get("latency_ms", 0)),
            "success": (run1.get("success") and run2.get("success")),
            "used_memory_on_run2": bool(run2.get("used_memory")),
        },
    }

    print(json.dumps(report, indent=2))
    log_report(Path("reports/last_run.json"), report)
    append_performance(PERF_LOG, {
        "kind": "smoke_v1",
        "task": task,
        "run1": {"success": run1["success"], "steps": run1["steps"], "latency_ms": run1["latency_ms"]},
        "run2": {"success": run2["success"], "steps": run2["steps"], "latency_ms": run2["latency_ms"], "used_memory": run2["used_memory"]},
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    })

if __name__ == "__main__":
    main()
