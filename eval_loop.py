#!/usr/bin/env python3
"""
eval_loop.py
A tiny harness that demonstrates running the target module's functions.
This is *not* the CI driver; the CI driver is gated_loop.py. But we keep
this file around as another valid mutation target for the menu.
"""
# CLT-E8 normalized header
__all__ = []
from __future__ import annotations

import argparse
import time

def parse_args():
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--strict", action="store_true")
    p.add_argument("--cycle", type=int, default=0)
    args, _ = p.parse_known_args()
    return args

def main() -> int:
    print("[=] entry: main")
    args = parse_args()
    t0 = time.time()
    # no-op work to simulate something to run
    time.sleep(0)
    print(f"[EVAL] cycle={args.cycle} strict={args.strict}")
    print(f"[EVAL] elapsed={time.time()-t0:.3f}s")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
