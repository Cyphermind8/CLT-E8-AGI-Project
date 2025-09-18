# FILE: src/memory/procedural_v1.py
from pathlib import Path
from typing import Dict, Any, List

class ProceduralMemory:
    """
    Stores named macros/skills. Not used by the smoke yet, but included to
    fulfill the run_smoke import contract and set the pattern.
    """

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.touch()

    def list_skills(self) -> List[str]:
        return []

    def save_skill(self, name: str, payload: Dict[str, Any]) -> None:
        import json
        row = {"name": name, "payload": payload}
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
