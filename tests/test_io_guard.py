from pathlib import Path
from src.governor import Governor, GovernorConfig

def test_allowlist_blocks_outside(tmp_path: Path):
    cfg = GovernorConfig(project_root=str(tmp_path), write_allow=("logs",))
    g = Governor(cfg)
    ok = tmp_path / "logs" / "ok.txt"
    g.write_text(str(ok), "ok")
    assert ok.read_text(encoding="utf-8") == "ok"

    blocked = tmp_path / "nope.txt"
    import pytest
    with pytest.raises(PermissionError):
        g.write_text(str(blocked), "nope")
