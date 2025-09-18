
# FILE: ci/continuous_improvement.py
#!/usr/bin/env python3
"""
CLT–E8 Continuous Improvement Orchestrator (Windows-friendly)

Fixes in this version
- Writes a session log **before** baselines so you can see progress even if baselines stall.
- Adds explicit baseline timeouts and console progress lines.
- Safer subprocess handling + clearer error messages.

Usage (PowerShell)
  .\.venv\Scripts\Activate
  $env:PYTHONPATH="."
  python ci\continuous_improvement.py --cycles 30 --time-budget-min 120

Kill switch: create STOP_CI.txt in project root.
"""

from __future__ import annotations
import argparse
import json
import os
import re
import sys
import time
import datetime as dt
import subprocess
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

ROOT = Path.cwd()
PYTHON = sys.executable or "python"
LOGS = ROOT / "logs"
REPORTS = ROOT / "reports"
STOP_FILE = ROOT / "STOP_CI.txt"
LOGS.mkdir(exist_ok=True, parents=True)
REPORTS.mkdir(exist_ok=True, parents=True)

def _ts() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")

def run(cmd: list, timeout: Optional[int] = None):
    """Run a subprocess and capture output; raise on timeout for clearer diagnosis."""
    try:
        proc = subprocess.run(
            cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout, shell=False
        )
        return proc.returncode, proc.stdout or "", proc.stderr or ""
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"[TIMEOUT] {' '.join(cmd)} (timeout={timeout}s)")

def _pick_latest(prefix: str) -> Optional[Path]:
    files = sorted(REPORTS.glob(f"{prefix}*.json"))
    return files[-1] if files else None

def _extract_json_path(output: str, key_prefix: str) -> Optional[str]:
    # match:  "json": "C:\\AI_Project\\reports\\bench_2025....json"
    m = re.search(rf'"json"\s*:\s*"([^"]*{re.escape(key_prefix)}[^"]*\.json)"', output)
    return m.group(1) if m else None

def ensure_baselines(determinism: int, runs: int, baseline_timeout: int, logger) -> Dict[str, str]:
    """Create fresh bench & micro baselines with timeouts; return their JSON paths."""
    artifacts: Dict[str, str] = {}

    logger("[CI] Seeding bench baseline...")
    code, out, err = run([PYTHON, "bench/run_bench.py", f"--determinism={determinism}"], timeout=baseline_timeout)
    if code != 0:
        raise RuntimeError(f"bench baseline failed (code={code}).\nSTDOUT:\n{out}\nSTDERR:\n{err}")
    bench_path = _extract_json_path(out, "bench_") or (_pick_latest("bench_") and str(_pick_latest("bench_")))
    if not bench_path:
        raise RuntimeError(f"bench baseline parse error. RAW:\n{out}")
    artifacts["bench_json"] = bench_path
    logger(f"[CI] Bench baseline OK: {bench_path}")

    logger("[CI] Seeding micro baseline...")
    code, out, err = run([PYTHON, "-m", "bench.run_workspace_micro", f"--runs={runs}"], timeout=baseline_timeout)
    if code != 0:
        raise RuntimeError(f"micro baseline failed (code={code}).\nSTDOUT:\n{out}\nSTDERR:\n{err}")
    micro_path = _extract_json_path(out, "micro_workspace_") or (_pick_latest("micro_workspace_") and str(_pick_latest("micro_workspace_")))
    if not micro_path:
        raise RuntimeError(f"micro baseline parse error. RAW:\n{out}")
    artifacts["micro_json"] = micro_path
    logger(f"[CI] Micro baseline OK: {micro_path}")

    return artifacts

def run_gated_loop(args, logger):
    """Execute one improvement cycle group. Returns (applied_any, raw_stdout)."""
    cmd = [
        PYTHON, "self_mod/gated_loop.py",
        "--target", str(args.target),
        "--population", str(args.population),
        "--determinism", str(args.determinism),
        "--bench-timeout", str(args.bench_timeout),
        "--pytest-timeout", str(args.pytest_timeout),
        "--min-rate", str(args.min_rate),
        "--min-equal-rate-speedup", str(args.min_equal_rate_speedup),
    ]
    if args.micro_gate:
        cmd += ["--micro-gate", "--micro-speedup", str(args.micro_speedup)]
    if args.skip_smoke:
        cmd += ["--skip-smoke"]

    code, out, err = run(cmd, timeout=args.cycle_timeout)
    raw = (out or "") + ("\n" + err if err else "")
    applied = "[Applied]" in raw
    if code != 0:
        logger(f"[CI] gated_loop exited with code {code}")
    return applied, raw

def main():
    ap = argparse.ArgumentParser(description="CLT-E8 Continuous Improvement Orchestrator")
    ap.add_argument("--target", default="src/workspace_v1.py", help="File under improvement")
    ap.add_argument("--population", type=int, default=2)
    ap.add_argument("--determinism", type=int, default=2)
    ap.add_argument("--bench-timeout", type=int, default=300)
    ap.add_argument("--pytest-timeout", type=int, default=120)
    ap.add_argument("--min-rate", type=float, default=1.0, help="Required bench accuracy rate")
    ap.add_argument("--min-equal-rate-speedup", type=float, default=0.02, help="Latency speedup if accuracy equal")
    ap.add_argument("--micro-gate", action="store_true")
    ap.add_argument("--micro-speedup", type=float, default=0.03)
    ap.add_argument("--skip-smoke", action="store_true")
    ap.add_argument("--cycles", type=int, default=20, help="Max cycles for this session")
    ap.add_argument("--sleep-sec", type=int, default=15, help="Pause between cycles")
    ap.add_argument("--max-no-apply", type=int, default=10, help="Stop if no accepted changes for N cycles")
    ap.add_argument("--max-fail", type=int, default=5, help="Stop if we see N consecutive failures")
    ap.add_argument("--time-budget-min", type=int, default=180, help="Stop after this many minutes")
    ap.add_argument("--cycle-timeout", type=int, default=3600, help="Hard timeout per gated_loop invocation (sec)")
    ap.add_argument("--baseline-timeout", type=int, default=900, help="Per-baseline hard timeout (sec)")
    args = ap.parse_args()

    # Create session log immediately
    session_ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    LOGS.mkdir(exist_ok=True, parents=True)
    REPORTS.mkdir(exist_ok=True, parents=True)
    log_path = LOGS / f"ci_session_{session_ts}.log"
    summary_path = REPORTS / f"ci_session_{session_ts}.json"
    LOG = open(log_path, "w", encoding="utf-8")

    def logger(msg: str):
        print(msg, flush=True)
        LOG.write(msg + "\n")
        LOG.flush()

    logger(f"[CI] Session {session_ts} starting in {ROOT}")

    start = time.time()
    no_apply_streak = 0
    fail_streak = 0
    applied_count = 0
    cycles_run = 0

    # Seed/refresh baselines
    try:
        logger("[CI] Seeding baselines... this may take a few minutes.")
        artifacts = ensure_baselines(args.determinism, runs=3, baseline_timeout=args.baseline_timeout, logger=logger)
        logger(f"[CI] Baselines ready: {artifacts}")
    except Exception as e:
        logger(f"[CI] Baseline setup failed: {e}")
        LOG.close()
        sys.exit(2)

    while cycles_run < args.cycles:
        if STOP_FILE.exists():
            logger("[CI] STOP_CI.txt detected, exiting.")
            break

        elapsed_min = (time.time() - start) / 60.0
        if elapsed_min >= args.time_budget_min:
            logger(f"[CI] Time budget reached ({elapsed_min:.1f} min), stopping.")
            break

        cycles_run += 1
        logger(f"\n[CI] --- Cycle {cycles_run}/{args.cycles} ---")

        try:
            applied, raw = run_gated_loop(args, logger)
        except RuntimeError as e:
            fail_streak += 1
            logger(f"[CI] gated_loop error: {e} (fail_streak={fail_streak})")
            if fail_streak >= args.max_fail:
                logger("[CI] Max fail streak reached; stopping.")
                break
            time.sleep(args.sleep_sec)
            continue

        trimmed = raw if len(raw) < 8000 else raw[:8000] + "\n...[trimmed]..."
        LOG.write(trimmed + "\n")
        LOG.flush()

        if applied:
            applied_count += 1
            no_apply_streak = 0
            fail_streak = 0
            logger(f"[CI] ✅ Applied improvement (total={applied_count})")
        else:
            no_apply_streak += 1
            logger(f"[CI] No apply this cycle (no_apply_streak={no_apply_streak})")

        if no_apply_streak >= args.max_no_apply:
            logger("[CI] No improvements for too long; stopping.")
            break

        time.sleep(args.sleep_sec)

    # Write summary
    summary = {
        "session": session_ts,
        "target": str(args.target),
        "cycles_run": cycles_run,
        "applied_count": applied_count,
        "no_apply_streak": no_apply_streak,
        "fail_streak": fail_streak,
        "time_minutes": round((time.time() - start) / 60.0, 2),
        "log_path": str(log_path),
    }
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    LOG.close()
    print(json.dumps({"summary_json": str(summary_path)}, indent=2))

if __name__ == "__main__":
    main()
