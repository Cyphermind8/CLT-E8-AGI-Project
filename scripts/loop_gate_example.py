# FILE: scripts/loop_gate_example.py (optional helper to call from your loop)
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOGS = ROOT / "logs"
BASE = LOGS / "metrics_latest.json"

def run_evals() -> Path:
    p = subprocess.run([sys.executable, "scripts/run_evals.py"], cwd=str(ROOT), capture_output=True, text=True)
    p.check_returncode()
    return Path(p.stdout.strip())

def promote_if(before: Path, after: Path, lines_changed: int = 8, lint_ok: bool = True) -> bool:
    rc = subprocess.call([
        sys.executable, "scripts/promote_if.py",
        "--before", str(before), "--after", str(after),
        "--lines-changed", str(lines_changed),
        "--lint-ok"
    ], cwd=str(ROOT))
    return rc == 0

def main():
    after = run_evals()
    if not BASE.exists():
        print("[decision] No baseline — approving seed.")
        BASE.write_text(after.read_text(encoding="utf-8"), encoding="utf-8")
        return 0
    if promote_if(BASE, after):
        BASE.write_text(after.read_text(encoding="utf-8"), encoding="utf-8")
        print("[decision] Baseline updated.")
    else:
        print("[decision] Rejected — keeping previous baseline.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())