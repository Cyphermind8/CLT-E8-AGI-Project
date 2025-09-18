from __future__ import annotations
import json, os, re, time, subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from src.io_guard import write_text, write_json
from src.utils.runlog import runlog, start_run, finish_run
from src.utils.gitwrap import ROOT, current_commit, create_branch, abort_changes, apply_patch, has_any_changes, commit_all
from src.auto.llm_client import chat
from src.clt_e8.policy import check_patch_stats, score_is_improvement

REPO_ROOT = ROOT

@dataclass
class BenchResult:
    pass_rate: float
    avg_latency: Optional[float]
    summary_path: Optional[Path]

def _latest_report_json() -> Optional[Path]:
    reports = Path(REPO_ROOT, "reports")
    if not reports.exists(): return None
    files = sorted(reports.glob("bench_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None

def _parse_report(p: Path) -> BenchResult:
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        s = data["summary"]
        passed = s["success"]["passed"]
        total  = s["success"]["total"]
        pr = (passed/total) if total else 0.0
        lat = s.get("latency",{}).get("avg_s")
        return BenchResult(pass_rate=pr, avg_latency=lat, summary_path=p)
    except Exception:
        return BenchResult(0.0, None, p)

def run_bench_and_read() -> BenchResult:
    # Use your wrapper (which writes reports/*)
    subprocess.run([str(Path(REPO_ROOT,".venv","Scripts","python.exe")),
                    str(Path(REPO_ROOT,"scripts","run_bench_with_log.py"))],
                    cwd=REPO_ROOT, check=True)
    p = _latest_report_json()
    return _parse_report(p) if p else BenchResult(0.0, None, None)

PROMPT_RULES = """You are a cautious code improver inside strict guardrails (CLT-E8 policy).
Make a SMALL, SAFE, UNIFIED DIFF PATCH that improves the benchmark pass rate and/or latency.
Rules:
- Change only files under src/, bench/, scripts/, tests/
- Do NOT touch src/governor.py, src/io_guard.py, src/utils/runlog.py, scripts/run_bench_with_log.py
- Keep changes minimal (a few dozen lines), focused, and reversible.
- The patch MUST be in standard unified diff format (with a/ and b/ prefixes).
- No prose, no code fences. Only the patch body.
Strategy:
- Consider the failing cases and suggest the smallest targeted fix.
- Prefer parameter tweaks, dispatch/argument normalization, or small helpers over large refactors.
"""

def _make_user_msg(prev: BenchResult) -> str:
    return f"""Current benchmark summary:
pass_rate={prev.pass_rate:.3f}, avg_latency={prev.avg_latency if prev.avg_latency is not None else "n/a"}.
Produce ONLY a unified diff patch. Nothing else."""

def propose_patch(prev: BenchResult) -> str:
    out = chat(PROMPT_RULES, _make_user_msg(prev), max_tokens=1200, temperature=0.2)
    # Strip accidental wrappers (code fences etc.)
    out = out.strip()
    # Common mistake: model adds <| or ``` markers; remove.
    out = re.sub(r"^```(?:diff)?|```$", "", out, flags=re.MULTILINE).strip()
    return out

def extract_patch_ok(patch_text: str) -> tuple[bool, str]:
    if not patch_text: return False, "Empty patch."
    # Basic sanity for unified diff
    if "diff --git " not in patch_text and ("--- " not in patch_text or "+++ " not in patch_text):
        return False, "Not a unified diff."
    ok, msg = check_patch_stats(patch_text)
    return ok, msg

def save_patch(run_dir: Path, patch_text: str) -> Path:
    patch_path = run_dir/"patch.diff"
    write_text(str(patch_path), patch_text)
    return patch_path

def improve_once() -> dict:
    rd = start_run({"phase":"self_improve"})
    try:
        baseline = run_bench_and_read()
        patch_text = propose_patch(baseline)
        ok, why = extract_patch_ok(patch_text)
        if not ok:
            write_json(str(rd/"result.json"), {"status":"reject_patch", "reason":why, "baseline":baseline.__dict__})
            return {"status":"reject_patch","reason":why}

        patch_path = save_patch(rd, patch_text)
        start_commit = current_commit()
        branch = f"auto/clt_e8_{time.strftime('%Y%m%d_%H%M%S')}"
        create_branch(branch)

        applied, msg = apply_patch(patch_path)
        if not applied:
            abort_changes(start_commit)
            write_json(str(rd/"result.json"), {"status":"apply_failed","git_msg":msg})
            return {"status":"apply_failed","git_msg":msg}

        # Quick safety: ensure tests pass before bench
        tests = subprocess.run(["pytest","-q"], cwd=REPO_ROOT, capture_output=True, text=True)
        if tests.returncode != 0:
            log = (tests.stdout or "") + "\n" + (tests.stderr or "")
            abort_changes(start_commit)
            write_json(str(rd/"result.json"), {"status":"tests_failed","pytest":log})
            return {"status":"tests_failed"}

        # Bench after tests
        after = run_bench_and_read()

        improved = score_is_improvement(baseline.pass_rate, after.pass_rate, baseline.avg_latency, after.avg_latency)
        if improved and has_any_changes():
            commit_all(f"auto: CLT-E8 small patch (pass_rate {baseline.pass_rate:.3f}->{after.pass_rate:.3f}, "
                       f"lat {baseline.avg_latency}->{after.avg_latency})")
            write_json(str(rd/"result.json"), {"status":"committed","branch":branch,
                                               "baseline":baseline.__dict__,"after":after.__dict__})
            return {"status":"committed","branch":branch,"after":after.pass_rate}
        else:
            abort_changes(start_commit)
            write_json(str(rd/"result.json"), {"status":"reverted","reason":"no_improvement",
                                               "baseline":baseline.__dict__,"after":after.__dict__})
            return {"status":"reverted","reason":"no_improvement"}
    finally:
        finish_run(rd, {"ok": True})
