from __future__ import annotations
import os, json, time, re
from statistics import mean, median
from pathlib import Path
from typing import Any, Dict, List, Tuple

from src.io_guard import write_json, write_text

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
RUNS = ROOT / "runs"
OUTDIR = REPORTS / "overnight"

def _load_reports(hours:int=36):
    items = []
    cutoff = time.time() - hours*3600
    for p in sorted(REPORTS.glob("bench_*.json"), key=lambda x: x.stat().st_mtime):
        try:
            with open(p, "r", encoding="utf-8") as f:
                doc = json.load(f)
            summ = (doc.get("outputs") or {}).get("summary") or {}
            if not summ:
                continue
            mtime = p.stat().st_mtime
            if mtime < cutoff:
                continue
            items.append((p, mtime, summ))
        except Exception:
            # skip malformed
            pass
    return items

def _pct(x): 
    return f"{100.0*x:.1f}%"

def main():
    reports = _load_reports(hours=36)
    now = time.strftime("%Y%m%d_%H%M%S")
    if not reports:
        text = "# Overnight Summary\n\nNo bench reports found in the last 36 hours.\n"
        write_text(str(OUTDIR / f"overnight_summary_{now}.md"), text)
        write_text(str(OUTDIR / "latest.md"), text)
        write_json(str(OUTDIR / f"overnight_summary_{now}.json"), {"runs":[]})
        write_json(str(OUTDIR / "latest.json"), {"runs":[]})
        print("No recent reports.")
        return

    rows = []
    per_test_ok: Dict[str, List[bool]] = {}
    per_test_lat: Dict[str, List[float]] = {}
    recent_fail_examples: Dict[str,str] = {}

    for p, mtime, s in reports:
        ts = s.get("timestamp") or time.strftime("%Y%m%d_%H%M%S", time.localtime(mtime))
        succ = s.get("success") or {}
        passed = succ.get("passed", 0)
        total = succ.get("total", 0)
        rate = float(succ.get("rate", 0.0))
        lat = (s.get("latency") or {}).get("avg_s", None)
        det_ok = bool(s.get("determinism_ok", False))
        rows.append({
            "file": str(p),
            "mtime": mtime,
            "timestamp": ts,
            "passed": passed,
            "total": total,
            "rate": rate,
            "avg_latency_s": lat,
            "determinism_ok": det_ok,
        })

        for r in (s.get("results") or []):
            name = r.get("name","?")
            ok = bool(r.get("ok", False))
            per_test_ok.setdefault(name, []).append(ok)
            if isinstance(r.get("latency_s"), (int,float)):
                per_test_lat.setdefault(name, []).append(float(r["latency_s"]))
            if not ok and isinstance(r.get("output"), str) and name not in recent_fail_examples:
                # grab a concise error message if present
                m = re.search(r"\[error\]\s*(.*)", r["output"], flags=re.I)
                recent_fail_examples[name] = (m.group(1) if m else r["output"])[:160]

    # overall stats
    rates = [r["rate"] for r in rows]
    lats = [r["avg_latency_s"] for r in rows if isinstance(r["avg_latency_s"], (int,float))]
    overall = {
        "runs_analyzed": len(rows),
        "rate_min": min(rates) if rates else None,
        "rate_median": median(rates) if rates else None,
        "rate_max": max(rates) if rates else None,
        "latency_avg_s_median": median(lats) if lats else None,
    }

    # flakies: tests that have both pass and fail across runs
    flakies = []
    for name, oks in per_test_ok.items():
        if any(oks) and not all(oks):
            flakies.append(name)
    flakies.sort()

    # slowest tests across runs (by mean latency)
    slow_tests = []
    for name, vals in per_test_lat.items():
        if vals:
            slow_tests.append((name, mean(vals)))
    slow_tests.sort(key=lambda x: x[1], reverse=True)
    slow_tests = slow_tests[:5]

    # assemble JSON
    agg = {
        "generated_at": now,
        "runs": rows,
        "overall": overall,
        "flaky_tests": flakies,
        "slow_tests_avg_latency": [{"name":n,"avg_latency_s":round(v,3)} for n,v in slow_tests],
        "recent_fail_examples": recent_fail_examples,
    }

    # write JSON + a friendly Markdown
    write_json(str(OUTDIR / f"overnight_summary_{now}.json"), agg)
    write_json(str(OUTDIR / "latest.json"), agg)

    # pretty markdown
    lines = []
    lines.append(f"# Overnight Summary — {now}")
    lines.append("")
    lines.append(f"- Runs analyzed: **{agg['overall']['runs_analyzed']}**")
    if rates:
        lines.append(f"- Pass rate min/median/max: **{_pct(overall['rate_min'])} / {_pct(overall['rate_median'])} / {_pct(overall['rate_max'])}**")
    if lats:
        lines.append(f"- Median avg-latency per run: **{overall['latency_avg_s_median']:.3f}s**")
    lines.append("")

    # recent runs table (last 10)
    lines.append("## Recent runs")
    lines.append("| timestamp | passed/total | pass rate | avg latency (s) | deterministic | report |")
    lines.append("|---|---:|---:|---:|:---:|:---|")
    for r in sorted(rows, key=lambda x: x["mtime"], reverse=True)[:10]:
        lines.append(f"| {r['timestamp']} | {r['passed']}/{r['total']} | {_pct(r['rate'])} | {r['avg_latency_s'] if r['avg_latency_s'] is not None else '-'} | {'✅' if r['determinism_ok'] else '⚠️'} | {Path(r['file']).name} |")

    # flakies
    lines.append("")
    lines.append("## Flaky tests (pass and fail across runs)")
    lines.append("- " + ("\n- ".join(flakies) if flakies else "None detected"))

    # slowest tests
    lines.append("")
    lines.append("## Slowest tests across runs (avg latency)")
    if slow_tests:
        lines.append("| test | avg latency (s) |")
        lines.append("|---|---:|")
        for n,v in slow_tests:
            lines.append(f"| {n} | {v:.3f} |")
    else:
        lines.append("No latency data found.")

    # recent failures
    lines.append("")
    lines.append("## Recent failure messages (first occurrence)")
    if recent_fail_examples:
        for n,msg in recent_fail_examples.items():
            lines.append(f"- **{n}** — `{msg}`")
    else:
        lines.append("No failures recorded in analyzed window.")

    md = "\n".join(lines) + "\n"
    write_text(str(OUTDIR / f"overnight_summary_{now}.md"), md)
    write_text(str(OUTDIR / "latest.md"), md)

    print("Wrote:", OUTDIR / f"overnight_summary_{now}.md")
    print("Also:", OUTDIR / "latest.md")

if __name__ == "__main__":
    main()
