from __future__ import annotations
import sys, os, time, json, subprocess
from pathlib import Path

# Project root resolved from this file location
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.utils.runlog import start_run, finish_run

def _run(cmd, cwd: Path) -> dict:
    t0 = time.time()
    try:
        cp = subprocess.run(cmd, cwd=str(cwd), stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True)
        ok = (cp.returncode == 0)
        out = cp.stdout or ""
        rc = cp.returncode
    except Exception as e:
        ok = False; out = f"[exception] {e}"; rc = -1
    return {
        "cmd": " ".join(cmd),
        "ok": ok,
        "returncode": rc,
        "seconds": round(time.time() - t0, 3),
        "tail": out[-2000:],  # last 2k chars
    }

def _latest_bench_report() -> dict | None:
    rep = ROOT / "reports"
    if not rep.exists(): return None
    js = sorted(rep.glob("bench_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not js: return None
    p = js[0]
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return {"path": str(p), "summary": data.get("summary", {})}
    except Exception:
        return {"path": str(p)}

def one_cycle(pause: int):
    rd = start_run({"runner": "overnight_ci", "pause_s": pause})
    try:
        steps = []
        steps.append(_run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT))
        steps.append(_run([sys.executable, "-m", "bench.run_bench"], cwd=ROOT))
        micro = ROOT / "bench" / "run_workspace_micro.py"
        if micro.exists():
            steps.append(_run([sys.executable, "-m", "bench.run_workspace_micro"], cwd=ROOT))
        rep = _latest_bench_report()
        finish_run(rd, {"ok": all(s["ok"] for s in steps), "steps": steps, "report": rep})
    finally:
        pass
    time.sleep(pause)

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=8.0, help="How long to run")
    ap.add_argument("--pause", type=int, default=300, help="Seconds between cycles")
    args = ap.parse_args()
    deadline = time.time() + args.hours * 3600
    while time.time() < deadline:
        one_cycle(args.pause)

if __name__ == "__main__":
    main()
