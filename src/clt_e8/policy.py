from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

# CLT-E8 policy hooks — small, reversible diffs; guard risky files
FORBIDDEN_GLOBS = (
    "src/governor.py", "src/io_guard.py", "src/utils/runlog.py",
    "scripts/run_bench_with_log.py", ".git/hooks/*",
)
ALLOWED_PREFIXES = ("src/", "bench/", "scripts/", "tests/")

@dataclass(frozen=True)
class PatchLimits:
    max_files: int = 4            # "energy budget": keep diffs small
    max_added_lines: int = 200
    max_removed_lines: int = 200

DEFAULT_LIMITS = PatchLimits()

def _matches_any(path: str, globs: Iterable[str]) -> bool:
    p = Path(path)
    for g in globs:
        if p.match(g):
            return True
    return False

def is_path_allowed(repo_rel: str) -> bool:
    if _matches_any(repo_rel, FORBIDDEN_GLOBS):
        return False
    return any(repo_rel.startswith(prefix) for prefix in ALLOWED_PREFIXES)

def score_is_improvement(prev_pass_rate: float, new_pass_rate: float, prev_latency: float | None, new_latency: float | None) -> bool:
    if new_pass_rate > prev_pass_rate:  # primary objective
        return True
    if new_pass_rate == prev_pass_rate and prev_pass_rate >= 0.9:
        # tie-break by latency when quality is already high
        if (prev_latency is not None) and (new_latency is not None) and (new_latency < prev_latency*0.98):
            return True
    return False

def check_patch_stats(patch_text: str, limits: PatchLimits = DEFAULT_LIMITS) -> tuple[bool, str]:
    files, add, rem = 0, 0, 0
    allowed_paths: list[str] = []
    for line in patch_text.splitlines():
        if line.startswith("+++ "):
            # e.g. "+++ b/src/foo.py"
            path = line.split("\t")[0].split(" ",2)[-1]
            if path.startswith("b/"):
                path = path[2:]
            if not is_path_allowed(path):
                return False, f"CLT-E8 policy: forbidden or outside allowed scope: {path}"
            allowed_paths.append(path)
            files += 1
        elif line.startswith("+") and not line.startswith("+++"):
            add += 1
        elif line.startswith("-") and not line.startswith("---"):
            rem += 1
    if files > limits.max_files: return False, f"Too many files modified: {files}>{limits.max_files}"
    if add > limits.max_added_lines: return False, f"Too many added lines: {add}>{limits.max_added_lines}"
    if rem > limits.max_removed_lines: return False, f"Too many removed lines: {rem}>{limits.max_removed_lines}"
    if not allowed_paths: return False, "No file changes detected in patch."
    return True, "ok"
