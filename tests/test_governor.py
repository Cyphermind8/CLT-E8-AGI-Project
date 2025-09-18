# FILE: tests/test_governor.py
from __future__ import annotations
import pytest
from pathlib import Path

from src.governor import Governor, GovernorConfig

def test_block_write_outside_allowlist(tmp_path: Path):
    root = tmp_path
    cfg = GovernorConfig(project_root=str(root), write_allow=("data",), dry_run=False)
    g = Governor(cfg)

    # Allowed: under data
    allowed = root / "data" / "ok.txt"
    g.write_text(str(allowed), "hello")
    assert allowed.read_text(encoding="utf-8") == "hello"

    # Blocked: root file
    blocked = root / "not_allowed.txt"
    with pytest.raises(PermissionError):
        g.write_text(str(blocked), "nope")

def test_dry_run_allows_nothing_is_written(tmp_path: Path):
    root = tmp_path
    cfg = GovernorConfig(project_root=str(root), write_allow=("reports",), dry_run=True)
    g = Governor(cfg)
    target = root / "reports" / "x.txt"
    g.write_text(str(target), "hello")
    assert not target.exists()

def test_append_and_json(tmp_path: Path):
    root = tmp_path
    cfg = GovernorConfig(project_root=str(root), write_allow=("logs", "reports"), dry_run=False)
    g = Governor(cfg)

    # append
    log = root / "logs" / "a.log"
    g.append_text(str(log), "L1\n")
    g.append_text(str(log), "L2\n")
    assert log.read_text(encoding="utf-8").splitlines() == ["L1", "L2"]

    # json
    rep = root / "reports" / "out.json"
    g.write_json(str(rep), {"b": 1, "a": 2})
    assert rep.read_text(encoding="utf-8").strip().startswith("{")
