"""
tms_lite_v1.py — Minimal contradiction tracker.
- Maintains a set of simple key->value 'facts'.
- Flags contradictions when a new assertion disagrees with an existing value.
- Returns a conflict list and exposes a normalized conflict 'mass' for coherence penalties.
"""

from typing import List, Tuple, Any, Dict

class TMSLite:
    def __init__(self):
        self.facts: Dict[str, Any] = {}   # key -> value

    def assert_fact(self, key: str, value: Any) -> List[Tuple[str, Any, Any]]:
        """Assert a fact; returns list of conflicts as (key, old_value, new_value)."""
        conflicts = []
        if key in self.facts and self.facts[key] != value:
            conflicts.append((key, self.facts[key], value))
        self.facts[key] = value
        return conflicts

    def conflict_mass(self, conflicts: List[Tuple[str, Any, Any]]) -> float:
        """Normalize conflicts to [0,1] by capping count (simple MVP heuristic)."""
        if not conflicts:
            return 0.0
        return min(1.0, len(conflicts) / 3.0)
