# FILE: src/memory/episodic_v1.py
from pathlib import Path
from typing import Dict, Any, Iterable

class EpisodicMemory:
    """
    Append-only JSONL episodes: each run writes one row.
    """

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.touch()

    def append(self, episode: Dict[str, Any]) -> None:
        import json
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(episode, ensure_ascii=False) + "\n")

    def iter(self) -> Iterable[Dict[str, Any]]:
        import json
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except Exception:
                    continue
