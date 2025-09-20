# FILE: src/learning_state.py
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, Tuple, List
import json, os, time

# Governor-safe writers & project root anchor
from src.io_guard import write_json, approved_targets

def _project_root() -> Path:
    roots = approved_targets()
    return Path(os.path.commonpath(roots)) if roots else Path.cwd()

def _anchor(p: Path | str) -> Path:
    p = Path(p)
    return p if p.is_absolute() else _project_root() / p

def _state_path() -> Path:
    return _anchor("data/learning_state.json")

# --- Public API ---

def load_learning_state() -> Dict[str, Any]:
    """Load persistent learning state (or return a fresh default)."""
    sp = _state_path()
    if sp.exists():
        # Reads are not restricted by Governor; safe to read directly.
        return json.loads(sp.read_text(encoding="utf-8"))
    # Fresh default
    now = time.time()
    return {
        "version": 1,
        "created_ts": now,
        "updated_ts": now,
        "coherence": {"score": 0.0, "history": []},   # running metrics
        "mutations": {"applied": 0, "accepted": 0},   # counters
        "notes": [],
    }

def save_learning_state(state: Dict[str, Any]) -> None:
    """Persist learning state with Governor-safe write."""
    state["updated_ts"] = time.time()
    write_json(str(_state_path()), state)

def apply_mutations(
    state: Dict[str, Any],
    decisions: List[Dict[str, Any]]
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Apply a batch of coherence-aligned 'decisions' (mutations).
    Returns (new_state, applied_decisions).
    This keeps logic conservative; your decision engine can evolve.
    """
    new_state = dict(state)
    applied: List[Dict[str, Any]] = []

    # Simple aggregator: count & record last decisions; decision engine
    # decides what to edit; this layer only books the results.
    for d in (decisions or []):
        # mark as applied; the executor will validate/commit code changes elsewhere
        applied.append({"id": d.get("id"), "kind": d.get("kind"), "status": "applied"})
        new_state["mutations"]["applied"] = int(new_state["mutations"].get("applied", 0)) + 1

    # Optional: update a coarse coherence trend if provided
    delta = 0.0
    for d in (decisions or []):
        if "coherence_delta" in d:
            try:
                delta += float(d["coherence_delta"])
            except Exception:
                pass

    hist = list(new_state["coherence"].get("history", []))
    new_score = float(new_state["coherence"].get("score", 0.0)) + delta
    new_state["coherence"]["score"] = new_score
    hist.append({"ts": time.time(), "delta": delta, "score": new_score})
    new_state["coherence"]["history"] = hist[-200:]  # keep recent window

    return new_state, applied
