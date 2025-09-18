# FILE: tests/test_run_contract.py
import json
from pathlib import Path
from typing import Any, Dict

from src.models.run_contract import RunResult
from src.workspace_v1 import Workspace
from src.memory.episodic_v1 import EpisodicMemory
from src.memory.semantic_v1 import SemanticMemory
from src.memory.procedural_v1 import ProceduralMemory

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
(DATA_DIR / "episodic.jsonl").touch(exist_ok=True)
(DATA_DIR / "semantic.jsonl").touch(exist_ok=True)
(DATA_DIR / "procedural.jsonl").touch(exist_ok=True)

def _validate_payload(payload: Dict[str, Any]) -> RunResult:
    model = RunResult(**payload)
    json.dumps(model.model_dump())  # must be serializable
    return model

def test_workspace_run_contract_smoke():
    ws = Workspace()
    episodic = EpisodicMemory(DATA_DIR / "episodic.jsonl")
    semantic = SemanticMemory(DATA_DIR / "semantic.jsonl")
    procedural = ProceduralMemory(DATA_DIR / "procedural.jsonl")

    payload = ws.run(
        "Compute 21 + 21 using available tools, verify, and record the method.",
        episodic=episodic,
        semantic=semantic,
        procedural=procedural,
    )
    model = _validate_payload(payload)

    assert isinstance(model.success, bool)
    assert model.steps >= 0
    assert model.latency_ms >= 0
    assert isinstance(model.used_memory, bool)
    assert isinstance(model.trace, list)
