from __future__ import annotations
import subprocess, os
from pathlib import Path

ROOT = Path(os.getenv("CLT_E8_PROJECT_ROOT", Path(__file__).resolve().parents[2]))

def run_git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=check)

def current_commit() -> str:
    return run_git("rev-parse","HEAD").stdout.strip()

def create_branch(name: str) -> None:
    run_git("checkout","-q","-b",name)

def abort_changes(to_commit: str) -> None:
    # hard reset to known commit and clean untracked files
    run_git("reset","-q","--hard", to_commit)
    run_git("clean","-qdf")

def apply_patch(patch_file: Path) -> tuple[bool, str]:
    cp = run_git("apply","--whitespace=nowarn","--index", str(patch_file), check=False)
    ok = (cp.returncode == 0)
    return ok, (cp.stderr or cp.stdout)

def has_any_changes() -> bool:
    return bool(run_git("status","--porcelain").stdout.strip())

def commit_all(message: str) -> None:
    run_git("add","-A")
    run_git("commit","-m", message)
