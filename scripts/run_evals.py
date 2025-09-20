# FILE: scripts/run_evals.py
from __future__ import annotations
import json, os, re, subprocess, sys, time
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LOGS = REPO / "logs"
LOGS.mkdir(parents=True, exist_ok=True)

def _run_pytest_quiet() -> tuple[str, float, int]:
    """Return (combined_output, duration_seconds, return_code)."""
    t0 = time.perf_counter()
    p = subprocess.run([sys.executable, "-m", "pytest", "-q"],
                       cwd=str(REPO), capture_output=True, text=True)
    dt = time.perf_counter() - t0
    out = (p.stdout or "") + "\n" + (p.stderr or "")
    return out, dt, p.returncode

_SUMMARY_RE = re.compile(
    r"(?:(?P<passed>\d+)\s+passed)?"
    r"(?:.*?(?P<failed>\d+)\s+failed)?"
    r"(?:.*?(?P<errors>\d+)\s+error[s]?)?"
    r"(?:.*?(?P<skipped>\d+)\s+skipped)?"
    r"(?:.*?(?P<xfail>\d+)\s+xfail)?"
    r"(?:.*?(?P<xpass>\d+)\s+xpass)?",
    re.IGNORECASE | re.DOTALL
)

def _parse_pass_total(text: str) -> tuple[int, int]:
    m = _SUMMARY_RE.search(text)
    if not m:
        return 0, 0
    g = {k:int(v) if v else 0 for k,v in m.groupdict().items()}
    total = g["passed"] + g["failed"] + g["errors"] + g["skipped"] + g["xfail"] + g["xpass"]
    return g["passed"], total

def main() -> int:
    # Run once for latency + metrics
    out1, dt1, rc1 = _run_pytest_quiet()
    p1, t1 = _parse_pass_total(out1)
    rate1 = (p1/t1) if t1 else 0.0

    # Run again to sanity-check determinism (pass/total stable)
    out2, dt2, rc2 = _run_pytest_quiet()
    p2, t2 = _parse_pass_total(out2)

    determinism_ok = (p1 == p2 and t1 == t2 and rc1 == rc2)

    metrics = {
        "success": {"passed": p1, "total": t1, "rate": round(rate1, 4)},
        "determinism_ok": bool(determinism_ok),
        "latency": {"avg_s": round(((dt1+dt2)/2.0), 3)},
        "summary_tail": "\n".join(out1.strip().splitlines()[-10:]),
        "ts": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = LOGS / f"metrics_{ts}.json"
    out.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (LOGS / "metrics_latest.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(str(out))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())