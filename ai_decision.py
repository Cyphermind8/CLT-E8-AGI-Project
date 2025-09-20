# FILE: ai_decision.py
"""CLT–E8 AGI • AIDecisionEngine (v2) — ranks by perf_gain, schema-consistent."""

from __future__ import annotations
import json, os
from typing import Dict, Any, List, Tuple

MEMORY_PATH = "ai_memory.json"

def _load_memory() -> Dict[str, Any]:
    if not os.path.exists(MEMORY_PATH):
        return {"modifications": [], "decisions": []}
    try:
        with open(MEMORY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {"modifications": [], "decisions": []}
            data.setdefault("modifications", [])
            data.setdefault("decisions", [])
            return data
    except Exception:
        return {"modifications": [], "decisions": []}

def _rank_mods(mods: List[Dict[str, Any]]) -> List[Tuple[float, str, Dict[str, Any]]]:
    ranked: List[Tuple[float, str, Dict[str, Any]]] = []
    for m in mods:
        file = m.get("file", "unknown.py")
        gain = float(m.get("perf_gain", 0.0) or 0.0)
        ranked.append((gain, file, m))
    ranked.sort(key=lambda t: (t[0], t[1]), reverse=True)
    return ranked

class AIDecisionEngine:
    def __init__(self):
        self.state = _load_memory()

    def propose_next(self) -> Dict[str, Any] | None:
        ranked = _rank_mods(self.state.get("modifications", []))
        if not ranked:
            print("⚠️ No modifications recorded yet; nothing to rank.")
            return None
        top = ranked[0][2]
        file = top.get("file", "unknown.py")
        gain = ranked[0][0]
        print(f"🚀 Selected next candidate from memory: {file} (perf_gain={gain:.3f})")
        return top

if __name__ == "__main__":
    dec = AIDecisionEngine()
    dec.propose_next()
