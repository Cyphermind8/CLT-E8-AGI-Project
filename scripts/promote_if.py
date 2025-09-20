# FILE: scripts/promote_if.py
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

# --- Robust repo-root import (works as file or module) ---
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# ---------------------------------------------------------

def load_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", type=Path, required=True)
    ap.add_argument("--after",  type=Path, required=True)
    ap.add_argument("--tool-before", type=Path)
    ap.add_argument("--tool-after",  type=Path)
    ap.add_argument("--lines-changed", type=int, default=0)
    ap.add_argument("--lint-ok", action="store_true")
    args = ap.parse_args()

    from src.ai_decision import decision

    before = load_json(args.before)
    after  = load_json(args.after)

    kw = {"lines_changed": args.lines_changed, "lint_ok": args.lint_ok}

    # Optional tool metrics (deltas)
    if args.tool_before and args.tool_after and args.tool_before.exists() and args.tool_after.exists():
        tb = load_json(args.tool_before); ta = load_json(args.tool_after)
        tool_gain   = float(ta.get("rate",0.0) - tb.get("rate",0.0))
        steps_delta = float(ta.get("avg_steps",0.0) - tb.get("avg_steps",0.0))
        cost_delta  = float(ta.get("avg_cost_chars",0.0) - tb.get("avg_cost_chars",0.0))
        kw.update({"tool_success_gain": tool_gain, "steps_delta": steps_delta, "cost_delta": cost_delta})

    rep = decision(before, after, **kw)
    print(f"[decision] approved={rep['approved']} score={rep.get('score'):.3f}")
    print(json.dumps(rep, indent=2))
    return 0 if rep.get("approved") else 1

if __name__ == "__main__":
    raise SystemExit(main())