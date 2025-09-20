# FILE: scripts/build_dashboard.py
from __future__ import annotations
import json, html
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
LOGS = ROOT / "logs"
rows = []
for p in sorted(LOGS.glob("metrics_*.json")):
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
        ts = obj.get("ts") or datetime.fromtimestamp(p.stat().st_mtime).isoformat()
        rate = obj.get("success",{}).get("rate")
        passed = obj.get("success",{}).get("passed")
        total = obj.get("success",{}).get("total")
        lat = obj.get("latency",{}).get("avg_s")
        det = obj.get("determinism_ok")
        rows.append((p.name, ts, rate, passed, total, lat, det))
    except Exception:
        continue

html_rows = "".join(
    f"<tr><td>{html.escape(name)}</td>"
    f"<td>{html.escape(ts)}</td>"
    f"<td>{rate:.3f}</td>"
    f"<td>{passed}/{total}</td>"
    f"<td>{'' if lat is None else f'{lat:.3f}s'}</td>"
    f"<td>{'✅' if det else '❌'}</td></tr>"
    for (name, ts, rate, passed, total, lat, det) in rows
)

doc = f"""<!DOCTYPE html>
<html><head><meta charset='utf-8'><title>CLT-E8 Dashboard</title>
<style>
body{{font-family:system-ui,Segoe UI,Arial,sans-serif;padding:16px}}
table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #ddd;padding:8px;text-align:left}}
th{{background:#f7f7f7}}
tr:nth-child(even){{background:#fafafa}}
</style></head>
<body>
<h2>CLT-E8 Metrics</h2>
<table>
<thead><tr><th>file</th><th>timestamp</th><th>rate</th><th>passed/total</th><th>latency</th><th>determinism</th></tr></thead>
<tbody>
{html_rows}
</tbody></table>
</body></html>"""

out = LOGS / "dashboard.html"
out.write_text(doc, encoding="utf-8")
print(str(out))
"""
Run:
  python scripts/build_dashboard.py
Then open the printed path in your browser.
"""