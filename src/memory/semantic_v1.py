# FILE: src/memory/semantic_v1.py
from pathlib import Path
from typing import Any, Dict, Optional

class SemanticMemory:
    """
    Tiny key-value store over JSONL where key is the task string.
    For the smoke test, this is enough to make run2 cheaper/faster.
    """

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.touch()

    def remember(self, key: str, value: Dict[str, Any]) -> None:
        import json
        row = {"key": key, "value": value}
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def lookup(self, key: str) -> Optional[Dict[str, Any]]:
        import json
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                for line in reversed(f.readlines()):
                    line = line.strip()
                    if not line:
                        continue
                    obj = json.loads(line)
                    if obj.get("key") == key:
                        return obj.get("value")
        except Exception:
            pass
        return None
