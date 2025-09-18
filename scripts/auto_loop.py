from __future__ import annotations
import argparse, time, os, sys
sys.path.insert(0, r"C:\AI_Project")
from src.auto.self_improver import improve_once
from src.utils.runlog import runlog

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iterations", type=int, default=20)
    ap.add_argument("--pause_s", type=int, default=300)  # gentle pacing
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()

    if args.once:
        with runlog({"runner":"auto_loop","mode":"once"}):
            print(improve_once())
        return

    with runlog({"runner":"auto_loop","mode":"loop"}):
        for i in range(args.iterations):
            print(f"[auto_loop] iteration {i+1}/{args.iterations}")
            result = improve_once()
            print(result)
            time.sleep(args.pause_s)

if __name__ == "__main__":
    main()
