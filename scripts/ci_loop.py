# FILE: scripts/ci_loop.py
from __future__ import annotations
import os, json, time, subprocess, sys, shutil
from pathlib import Path
from datetime import datetime, timedelta

WS = Path(__file__).resolve().parents[1]
LOGS = WS / "logs"
REPORTS = WS / "reports"
LOGS.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)

def ts() -> str: return time.strftime("%Y%m%d_%H%M%S")

def run(cmd: list[str], cwd: Path, stdout: Path, stderr: Path, timeout_s: int) -> dict:
    with stdout.open("wb") as out, stderr.open("wb") as err:
        try:
            p = subprocess.run(cmd, cwd=str(cwd), stdout=out, stderr=err, timeout=timeout_s, check=False)
            exitcode = p.returncode
            hard_timeout = False
        except subprocess.TimeoutExpired:
            hard_timeout = True
            exitcode = 124
        return {"exitcode": exitcode, "hard_timeout": hard_timeout}

def file_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore") if p.exists() else ""

def seed_baselines(pytest_timeout=120, bench_timeout=300) -> None:
    # Simple seed using your existing run_all.ps1 for consistency
    log = LOGS / f"run_all_{ts()}.log"
    with log.open("wb") as out:
        subprocess.run(["powershell","-NoProfile","-ExecutionPolicy","Bypass","-File", str(WS/"scripts/run_all.ps1")],
                       cwd=str(WS), stdout=out, stderr=out, timeout=pytest_timeout+bench_timeout, check=False)
    print(f"[seed] run_all log: {log}")

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--cycles", type=int, default=6)
    ap.add_argument("--timebudget_min", type=int, default=30)
    ap.add_argument("--percycle", type=int, default=240, help="hard timeout per cycle (seconds)")
    ap.add_argument("--det", type=int, default=2)
    ap.add_argument("--pop", type=int, default=2)
    ap.add_argument("--min_rate", type=float, default=1.0)
    ap.add_argument("--equal_speed", type=float, default=0.03)
    ap.add_argument("--micro_gate", action="store_true")
    ap.add_argument("--micro_speed", type=float, default=0.03)
    ap.add_argument("--bench_timeout", type=int, default=300)
    ap.add_argument("--pytest_timeout", type=int, default=120)
    args = ap.parse_args()

    session_stamp = ts()
    session_log = LOGS / f"ci_py_session_{session_stamp}.log"
    session_json = REPORTS / f"ci_py_session_{session_stamp}.json"

    with session_log.open("w", encoding="utf-8") as slog:
        print(f"[{time.strftime('%H:%M:%S')}] [CI] session {session_stamp} in {WS}", file=slog, flush=True)
        print(f"[{time.strftime('%H:%M:%S')}] [CI] seeding baselines…", file=slog, flush=True)

    seed_baselines(args.pytest_timeout, args.bench_timeout)

    deadline = datetime.now() + timedelta(minutes=args.timebudget_min)
    targets = [r"src\llm\planner_llm.py", r"src\llm\critic_llm.py", r"src\workspace_v1.py"]
    accepted = rejected = failed = 0
    items: list[dict] = []

    cycle = 0
    while cycle < args.cycles and datetime.now() < deadline:
        cycle += 1
        for t in targets:
            glstamp = ts()
            out = LOGS / f"gated_loop_{glstamp}.out.log"
            err = LOGS / f"gated_loop_{glstamp}.err.log"
            cmd = [
                sys.executable, "self_mod/gated_loop.py",
                "--target", t,
                "--population", str(args.pop),
                "--determinism", str(args.det),
                "--bench-timeout", str(args.bench_timeout),
                "--pytest-timeout", str(args.pytest_timeout),
                "--min-rate", str(args.min_rate),
                "--min-equal-rate-speedup", str(args.equal_speed),
            ]
            if args.micro_gate:
                cmd += ["--micro-gate", "--micro-speedup", str(args.micro_speed)]

            with session_log.open("a", encoding="utf-8") as slog:
                print(f"[{time.strftime('%H:%M:%S')}] [Cycle {cycle}] launching: {' '.join(cmd)}", file=slog, flush=True)

            r = run(cmd, WS, out, err, timeout_s=args.percycle)
            text = file_text(out) + file_text(err)
            gl_all = LOGS / f"gated_loop_{glstamp}.log"
            gl_all.write_text(text, encoding="utf-8")

            accepted_patch = ("Candidate PASSED all gates" in text) or ("[Applied]" in text)
            no_change = "No-op/cosmetic change detected" in text
            pytest_fail = "[Gate] pytest failed" in text
            bench_fail = "[Gate] [Bench]" in text
            micro_fail = ("[Micro]" in text) and ("not fast enough" in text or "failed" in text)

            if accepted_patch: accepted += 1
            elif no_change:    rejected += 1
            else:              failed += 1

            items.append({
                "log": str(gl_all),
                "accepted": accepted_patch,
                "nochange": no_change,
                "pytest": pytest_fail,
                "bench": bench_fail,
                "micro": micro_fail,
                "hard_timeout": bool(r["hard_timeout"]),
                "exit": int(r["exitcode"]),
            })

            with session_log.open("a", encoding="utf-8") as slog:
                print(f"[{time.strftime('%H:%M:%S')}] [Cycle {cycle}] result: "
                      f"accepted={accepted_patch} nochange={no_change} pytest={pytest_fail} "
                      f"bench={bench_fail} micro={micro_fail} hardtimeout={r['hard_timeout']} "
                      f"exit={r['exitcode']} log={gl_all}", file=slog, flush=True)

            if datetime.now() >= deadline:
                break

    summary = {
        "timestamp": session_stamp,
        "cycles": cycle,
        "accepted": accepted,
        "rejected": rejected,
        "failed": failed,
        "logs": [it["log"] for it in items],
    }
    session_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    with session_log.open("a", encoding="utf-8") as slog:
        print(f"[{time.strftime('%H:%M:%S')}] [CI] finished. Summary: {session_json}", file=slog, flush=True)
    print(json.dumps({"summary_json": str(session_json), "session_log": str(session_log)}, indent=2))

if __name__ == "__main__":
    main()
