# FILE: bench/run_workspace_micro.py
from __future__ import annotations
import argparse, json, time
from pathlib import Path
from typing import Dict, Any, List
from importlib import import_module

REPORTS = Path("reports"); REPORTS.mkdir(parents=True, exist_ok=True)

def nowstamp() -> str: return time.strftime("%Y%m%d_%H%M%S")

# ---- Safe fallback memories (used only if imports fail) ----
class _EpisodicStub:
    def __init__(self, _: Path): pass
    def append(self, episode: Dict[str, Any]) -> None: pass

class _SemanticStub:
    def __init__(self, _: Path): self._mem: Dict[str, Any] = {}
    def lookup(self, key: str): return self._mem.get(key)
    def remember(self, key: str, value: Any) -> None: self._mem[key] = value

class _ProceduralStub:
    def __init__(self, _: Path): pass

def _load_memories() -> Dict[str, Any]:
    # Try real modules first; fall back to stubs if not found
    try:
        mem_e = import_module("episodic_v1"); Episodic = getattr(mem_e, "EpisodicMemory")
    except Exception:
        Episodic = _EpisodicStub
    try:
        mem_s = import_module("semantic_v1"); Semantic = getattr(mem_s, "SemanticMemory")
    except Exception:
        Semantic = _SemanticStub
    try:
        mem_p = import_module("procedural_v1"); Procedural = getattr(mem_p, "ProceduralMemory")
    except Exception:
        Procedural = _ProceduralStub
    data = Path("data"); data.mkdir(exist_ok=True)
    return dict(
        episodic=Episodic(data / "episodic.jsonl"),
        semantic=Semantic(data / "semantic.jsonl"),
        procedural=Procedural(data / "procedural.jsonl"),
    )

def run_once(workspace, task: str, memories) -> Dict[str, Any]:
    t0 = time.perf_counter()
    res = workspace.run(task, **memories)
    t1 = time.perf_counter()
    # Harden metrics
    if "latency_ms" not in res:
        res["latency_ms"] = round((t1 - t0) * 1000.0, 3)
    if "steps" not in res:
        res["steps"] = len(res.get("trace", []))
    return res

def main(runs: int = 3) -> Dict[str, Any]:
    # Late import to avoid side effects
    ws_mod = import_module("src.workspace_v1")
    workspace = ws_mod.Workspace()
    memories = _load_memories()

    tasks = [
        "Compute 21 + 21 using available tools, verify, and record the method.",
        "Compute 34 + 55 using available tools, verify, and record the method.",
    ]
    results: Dict[str, Any] = {t: [] for t in tasks}

    for t in tasks:
        for _ in range(runs):
            r = run_once(workspace, t, memories)
            results[t].append(r)

    def agg(rs: List[Dict[str, Any]]) -> Dict[str, Any]:
        lat = [float(r["latency_ms"]) for r in rs]
        stp = [int(r["steps"]) for r in rs]
        ok = [bool(r.get("success", False)) for r in rs]
        return {
            "runs": len(rs),
            "avg_steps": round(sum(stp) / len(stp), 2),
            "avg_latency_ms": round(sum(lat) / len(lat), 3),
            "all_ok": all(ok),
        }

    summary = {
        "timestamp": nowstamp(),
        "runs_per_task": runs,
        "tasks": {t: agg(results[t]) for t in tasks},
    }
    t_agg = [agg(results[t]) for t in tasks]
    summary["aggregate"] = {
        "avg_steps": round(sum(x["avg_steps"] for x in t_agg) / len(t_agg), 2),
        "avg_latency_ms": round(sum(x["avg_latency_ms"] for x in t_agg) / len(t_agg), 3),
        "all_ok": all(x["all_ok"] for x in t_agg),
    }

    out = {
        "outputs": {
            "json": str(REPORTS / f"micro_workspace_{summary['timestamp']}.json"),
            "summary": summary,
        }
    }
    with open(out["outputs"]["json"], "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return out

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=5)
    main(parser.parse_args().runs)
