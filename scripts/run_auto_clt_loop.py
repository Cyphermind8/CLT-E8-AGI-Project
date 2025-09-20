# FILE: scripts/run_auto_clt_loop.py
from __future__ import annotations

import argparse
import json
import sys
import os
import time
from typing import Any, Dict

# --- make sure imports work no matter where we launch from ---
ROOT = r"C:\AI_Project"
if os.path.isdir(ROOT) and ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.utils.runlog import runlog, start_run, finish_run
from src.io_guard import write_json, append_text
from scripts.auto_clt_loop import auto_loop  # our loop core


def _log(rd: str, line: str) -> None:
    """Append a single line to run.log with timestamp."""
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    append_text(os.path.join(rd, "run.log"), f"[{stamp}] {line}\n")


def _summarize(rd: str, payload: Dict[str, Any]) -> None:
    """Write a compact JSON summary for this cycle."""
    write_json(os.path.join(rd, "summary.json"), payload)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--hours", type=float, default=10.0, help="Total wall time to run.")
    p.add_argument("--pause-seconds", type=int, default=300, help="Pause between cycles.")
    p.add_argument("--max-cycles", type=int, default=0, help="Optional hard cap on number of cycles (0 = unlimited within hours).")
    args = p.parse_args()

    t_end = time.time() + (args.hours * 3600.0)
    cycle = 0

    while time.time() < t_end:
        cycle += 1
        if args.max_cycles and cycle > args.max_cycles:
            break

        # Each cycle gets its own run dir & logs via runlog()
        meta = {
            "runner": "auto_clt_loop",
            "cycle": cycle,
            "pause_s": args.pause_seconds,
            "ts_start": time.time(),
        }

        with runlog(meta) as rd_path:
            rd = str(rd_path)
            try:
                _log(rd, f"=== CYCLE {cycle} start ===")
                decision = auto_loop()  # must return a dict with approved/score/... (as you printed earlier)
                # Echo to console and file
                print(json.dumps(decision, indent=2))
                _log(rd, f"[decision] approved={decision.get('approved')} score={decision.get('score')}")
                # Persist a compact summary for this cycle
                _summarize(rd, {
                    "cycle": cycle,
                    "decision": decision,
                    "ts_end": time.time(),
                })
                _log(rd, f"=== CYCLE {cycle} end; sleeping {args.pause_seconds}s ===")
            except Exception as e:
                # Never kill the session; log error, write summary, continue
                _log(rd, f"[ERROR] {type(e).__name__}: {e}")
                _summarize(rd, {
                    "cycle": cycle,
                    "error": f"{type(e).__name__}: {e}",
                    "ts_end": time.time(),
                })

        # Respect pause if there’s still time left
        if time.time() + args.pause_seconds > t_end:
            break
        time.sleep(args.pause_seconds)

    print("auto_clt_loop: DONE")


if __name__ == "__main__":
    main()
