# FILE: self_mod/continuous_improvement.py
"""
CLT–E8 Hands-Off Continuous Improvement Driver

What it does
- Health-checks your local OpenAI-compatible server (LM Studio).
- Seeds fresh baselines (bench + micro) to lock a comparison point.
- Runs self_mod/gated_loop.py repeatedly with guardrails:
  * Time budget OR fixed cycle count.
  * Tolerant of transient timeouts (cycle keeps going).
  * Tracks "no apply" streak to avoid spinning forever.

No external deps beyond stdlib. Reads OPENAI_* from env or your .env via downstream code.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from glob import glob
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
LOGS = ROOT / "logs"
REPORTS.mkdir(exist_ok=True, parents=True)
LOGS.mkdir(exist_ok=True, parents=True)

def say(msg: str) -> None:
    print(f"[CI] {msg}", flush=True)

def run(cmd: list[str], timeout: int | None = None) -> tuple[int, str, str]:
    """Run a subprocess and capture output; never throws on non-zero."""
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=str(ROOT))
    try:
        out, err = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        p.kill()
        return 124, "", f"TimeoutExpired after {timeout}s"
    return p.returncode, out.decode("utf-8", errors="replace"), err.decode("utf-8", errors="replace")

def latest(path_glob: str) -> str | None:
    files = sorted(glob(path_glob), key=lambda p: Path(p).stat().st_mtime)
    return files[-1] if files else None

def health_check() -> None:
    base = os.getenv("OPENAI_BASE_URL", "http://127.0.0.1:1234/v1").rstrip("/")
    url = f"{base}/models"
    say(f"Probing {url} …")
    try:
        with urlopen(Request(url, headers={"Accept": "application/json"}), timeout=5) as r:
            _ = r.read()
        say("LLM server is reachable.")
    except URLError as e:
        raise SystemExit(f"[CI] LLM server not reachable at {url}: {e}")

def seed_baselines(determinism: int) -> dict:
    say("Seeding baselines… this may take a minute.")
    # Bench baseline
    rc, out, err = run([sys.executable, "bench/run_bench.py", f"--determinism={determinism}"])
    if rc != 0:
        raise SystemExit(f"[CI] bench baseline failed (rc={rc}):\nSTDOUT:\n{out}\nSTDERR:\n{err}")
    bench_json = latest(str(REPORTS / "bench_*.json"))
    if not bench_json: raise SystemExit("[CI] No bench_* baseline JSON found in reports/")
    say(f"Bench baseline OK: {bench_json}")

    # Micro baseline
    rc, out, err = run([sys.executable, "-m", "bench.run_workspace_micro", "--runs", "3"])
    if rc != 0:
        raise SystemExit(f"[CI] micro baseline failed (rc={rc}):\nSTDOUT:\n{out}\nSTDERR:\n{err}")
    micro_json = latest(str(REPORTS / "micro_workspace_*.json"))
    if not micro_json: raise SystemExit("[CI] No micro_workspace_* JSON found in reports/")
    say(f"Micro baseline OK: {micro_json}")

    return {"bench_json": bench_json, "micro_json": micro_json}

def detect_apply(stdout_text: str) -> bool:
    # Conservative: look for explicit apply line from gated_loop
    tokens = ["[Applied]", "Candidate PASSED all gates", "target updated"]
    return any(t in stdout_text for t in tokens)

def run_cycle(args, baselines: dict, session_log: Path) -> tuple[bool, int, str]:
    """Returns (applied, rc, reason) for one gated_loop invocation."""
    gl_args = [
        sys.executable, "self_mod/gated_loop.py",
        "--target", args.target,
        "--population", str(args.population),
        "--determinism", str(args.determinism),
        "--bench-timeout", str(args.bench_timeout),
        "--pytest-timeout", str(args.pytest_timeout),
        "--min-rate", str(args.min_rate),
        "--min-equal-rate-speedup", str(args.min_equal_rate_speedup),
    ]
    if args.micro_gate:
        gl_args += ["--micro-gate", "--micro-speedup", str(args.micro_speedup)]
    if args.skip_smoke:
        gl_args += ["--skip-smoke"]

    # Export baseline hints for gated_loop implementations that consume env
    env = os.environ.copy()
    env["BENCH_BASELINE_JSON"] = baselines["bench_json"]
    env["MICRO_BASELINE_JSON"] = baselines["micro_json"]

    rc, out, err = run(gl_args, timeout=args.cycle_timeout or None)
    with session_log.open("a", encoding="utf-8") as f:
        f.write("\n=== gated_loop stdout ===\n"); f.write(out)
        f.write("\n=== gated_loop stderr ===\n"); f.write(err)

    if rc == 124:
        return (False, rc, "cycle timeout")
    if "APITimeoutError" in err or "ConnectTimeout" in err or "Request timed out" in out:
        return (False, 1, "LLM timeout")
    applied = detect_apply(out)
    return (applied, rc, "applied" if applied else "no-apply")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="src/workspace_v1.py")
    ap.add_argument("--cycles", type=int, default=30)
    ap.add_argument("--time-budget-min", type=int, default=180)
    ap.add_argument("--population", type=int, default=2)
    ap.add_argument("--determinism", type=int, default=2)
    ap.add_argument("--bench-timeout", type=int, default=300)
    ap.add_argument("--pytest-timeout", type=int, default=120)
    ap.add_argument("--min-rate", type=float, default=1.0)
    ap.add_argument("--min-equal-rate-speedup", type=float, default=0.03)
    ap.add_argument("--micro-gate", action="store_true")
    ap.add_argument("--micro-speedup", type=float, default=0.03)
    ap.add_argument("--skip-smoke", action="store_true")
    ap.add_argument("--sleep-sec", type=int, default=5)
    ap.add_argument("--max-no-apply", type=int, default=12)
    ap.add_argument("--max-fail", type=int, default=8)
    ap.add_argument("--cycle-timeout", type=int, default=0)
    args = ap.parse_args()

    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_log = LOGS / f"ci_session_{session_id}.log"
    with session_log.open("w", encoding="utf-8") as f:
        f.write(f"[CI] Session {session_id} starting in {ROOT}\n")

    say(f"Session {session_id} starting in {ROOT}")
    health_check()

    baselines = seed_baselines(args.determinism)
    say(f"Baselines ready: {json.dumps(baselines)}")

    deadline = datetime.now() + timedelta(minutes=args.time_budget_min)
    no_apply_streak = 0
    fail_streak = 0
    applied_count = 0
    total_cycles = 0

    for i in range(1, args.cycles + 1):
        if datetime.now() > deadline:
            say("Time budget reached; stopping.")
            break
        say(f"--- Cycle {i}/{args.cycles} ---")
        applied, rc, reason = run_cycle(args, baselines, session_log)
        total_cycles += 1

        if rc == 0 and applied:
            applied_count += 1
            no_apply_streak = 0
            say("✅ Applied improvement this cycle.")
            # Update baselines only after a successful apply, so future cycles compare to the new state
            baselines = seed_baselines(args.determinism)
        elif rc == 0 and not applied:
            no_apply_streak += 1
            say(f"No apply this cycle (no_apply_streak={no_apply_streak})")
        else:
            fail_streak += 1
            say(f"gated_loop exited with code {rc} ({reason}); fail_streak={fail_streak}")

        if no_apply_streak >= args.max_no_apply:
            say("No improvements for too long; stopping.")
            break
        if fail_streak >= args.max_fail:
            say("Too many failures; stopping.")
            break

        time.sleep(args.sleep_sec)

    # Write summary artifact
    summary = {
        "session": session_id,
        "applied": applied_count,
        "cycles_run": total_cycles,
        "stopped_reason": "budget/limit" if total_cycles >= args.cycles or datetime.now() > deadline else "early_stop",
        "baselines": baselines
    }
    out_json = REPORTS / f"ci_session_{session_id}.json"
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({"summary_json": str(out_json)}, indent=2))
    # Exit with 0 — CI completion isn't an error even if no applies.
    sys.exit(0)

if __name__ == "__main__":
    main()
