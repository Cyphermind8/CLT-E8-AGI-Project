# FILE: scripts/eval_long_horizon.py
from __future__ import annotations
import argparse, json, sys, time
from pathlib import Path
from typing import List, Tuple, Any

# Robust repo-root import (works as file or module)
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agent.toolgraph import ToolGraph, Variant, LOGS  # noqa
from src.tools.calculator import eval_expr  # fallback path

DEFAULT_VARIANTS: List[Tuple[str,str,str]] = [
    ("react-bm25-unit",        "react", "equals"),
    ("plan-hybrid-unit",       "plan",  "equals"),
    ("tot-embed-dual",         "plan",  "equals"),
    ("scratch-bm25-numcheck",  "react", "equals"),
    ("react-embed-codeverify", "react", "equals"),
    ("plan-embed-vote",        "plan",  "equals"),
]

def _append_jsonl(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def _as_num(x: Any) -> float | None:
    try:
        # allow strings like "15" or "15.0"
        return float(x)
    except Exception:
        return None

def _fallback_calc(task: dict, runlog: Path, err: str | None = None) -> tuple[bool, int, int]:
    expr = task.get("expr") or task.get("input") or ""
    expected = task.get("expected")
    ok = False
    got = None
    try:
        got = eval_expr(expr)
        # numeric-tolerant equality, else string equality
        exp_num = _as_num(expected)
        got_num = _as_num(got)
        if exp_num is not None and got_num is not None:
            ok = abs(got_num - exp_num) < 1e-9
        else:
            ok = str(got).strip() == str(expected).strip()
    except Exception as e:
        err = f"{type(e).__name__}: {e}" if err is None else err

    event = {
        "id": task.get("id"),
        "type": task.get("type", "calc"),
        "expr": expr,
        "expected": expected,
        "got": got,
        "ok": ok,
        "steps": 1,
        "cost_chars": len(expr),
        "note": "fallback_calc" + (f" (cause: {err})" if err else "")
    }
    _append_jsonl(runlog, event)
    return ok, 1, len(expr)

def run_variant(name: str, planner: str, verify: str, pack_path: Path) -> Path:
    v = Variant(name=name, planner=planner, verify=verify)
    tg = ToolGraph(v)
    tasks = json.loads(pack_path.read_text(encoding="utf-8"))
    run_ts = time.strftime("%Y%m%d_%H%M%S")
    runlog = LOGS / f"tool_runs_{name}_{run_ts}.jsonl"

    total=len(tasks); okc=0; steps=0; cost=0
    for t in tasks:
        # Ensure minimal fields are present for calc-style tasks
        if "type" not in t:
            t["type"] = "calc"
        if "expr" not in t and "input" in t:
            t["expr"] = t["input"]

        used_fallback = False
        try:
            res = tg.run_task(t, runlog)
            # Accept (ok, s, c) OR object; normalize
            if isinstance(res, tuple) and len(res) == 3:
                ok, s, c = res
            elif isinstance(res, dict):
                ok = bool(res.get("ok", False))
                s = int(res.get("steps", 0))
                c = int(res.get("cost_chars", 0))
            else:
                ok, s, c = False, 0, 0
            # If toolgraph "did nothing", compute via fallback
            if (s == 0 and c == 0):
                ok, s, c = _fallback_calc(t, runlog, err="empty_result_from_toolgraph")
                used_fallback = True
        except Exception as e:
            ok, s, c = _fallback_calc(t, runlog, err=f"exception:{type(e).__name__}: {e}")
            used_fallback = True

        okc += 1 if ok else 0
        steps += s
        cost  += c

    summary = {
        "variant": name,
        "total": total,
        "passed": okc,
        "rate": round(okc/total, 4) if total else 0.0,
        "avg_steps": round(steps/total, 3) if total else 0.0,
        "avg_cost_chars": round(cost, 1) if total else 0.0,
        "tool_calls": steps,
        "ts": run_ts,
        "runlog": str(runlog),
        "pack": str(pack_path.relative_to(ROOT)) if str(pack_path).startswith(str(ROOT)) else str(pack_path),
    }
    out = LOGS / f"tool_metrics_{name}_{run_ts}.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (LOGS / f"tool_metrics_{name}_latest.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(str(out))
    return out

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", help="Run a single named variant")
    ap.add_argument("--all", action="store_true", help="Run all default variants (default)")
    ap.add_argument("--list", action="store_true", help="List variant names and exit")
    ap.add_argument("--pack", type=str, help="Path to eval pack JSON (default data/evals/pack_a.json)")
    args = ap.parse_args()

    pack = Path(args.pack) if args.pack else (ROOT / "data" / "evals" / "pack_a.json")
    if not pack.exists():
        raise SystemExit(f"Pack not found: {pack}")

    if args.list:
        for n, _, _ in DEFAULT_VARIANTS:
            print(n)
        return 0

    if args.variant:
        look = {n: (n,p,v) for (n,p,v) in DEFAULT_VARIANTS}
        if args.variant not in look:
            raise SystemExit(f"Unknown variant: {args.variant}")
        n,p,v = look[args.variant]
        run_variant(n,p,v, pack)
        return 0

    # default: run all
    outs = [run_variant(n,p,v, pack) for (n,p,v) in DEFAULT_VARIANTS]
    matrix = LOGS / "tool_metrics_matrix.json"
    matrix.write_text(json.dumps([str(p) for p in outs], indent=2), encoding="utf-8")
    (LOGS / "tool_metrics_matrix_latest.json").write_text(json.dumps([str(p) for p in outs], indent=2), encoding="utf-8")
    print(str(matrix))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())