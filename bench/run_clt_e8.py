from __future__ import annotations
import json, time, os
from pathlib import Path
from clt_e8.probes import run_all

def _ts() -> str:
    return time.strftime("%Y%m%d_%H%M%S", time.localtime())

def main():
    ws = Path(os.getcwd())
    reports = ws / "reports"
    reports.mkdir(parents=True, exist_ok=True)

    # LLM mode: set CLT_E8_USE_LLM="1" before running.
    enabled = os.getenv("CLT_E8_USE_LLM", "0") in ("1","true","True")
    score, results = run_all(enabled)

    stamp = _ts()
    out_json = reports / f"clt_e8_{stamp}.json"
    out_md   = reports / f"clt_e8_{stamp}.md"

    jd = {
        "timestamp": stamp,
        "enabled": enabled,
        "score": round(float(score), 3),
        "results": [{"name":r.name,"ok":bool(r.ok),"explain":r.explain} for r in results],
    }
    out_json.write_text(json.dumps(jd, indent=2), encoding="utf-8")

    lines = [
        f"# CLT-E8 report {stamp}",
        f"- enabled: {enabled}",
        f"- score: {jd['score']}",
        "## Results:",
    ] + [f"- {r['name']}: {'OK' if r['ok'] else 'NO'} — {r['explain']}" for r in jd["results"]]
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"outputs":{"json":str(out_json),"md":str(out_md),"score":jd["score"],"enabled":enabled}}, indent=2))

if __name__ == "__main__":
    main()
