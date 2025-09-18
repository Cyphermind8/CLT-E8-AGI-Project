from pathlib import Path
from src.utils.runlog import start_run, finish_run

def test_runlog(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    rd = start_run({"foo":"bar"})
    assert rd.exists()
    finish_run(rd, {"ok": True})
    assert (rd/"summary.json").exists()
