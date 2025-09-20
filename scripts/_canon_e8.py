from pathlib import Path
import json
from src.tools.calculator import eval_expr

root = Path.cwd()
inp  = root / "data" / "evals" / "pack_e8.json"
out  = root / "data" / "evals" / "pack_e8_canonical.json"

items = json.loads(inp.read_text(encoding="utf-8"))
fixed, diffs = [], 0
for t in items:
    t.setdefault("type", "calc")
    if "expr" not in t and "input" in t:
        t["expr"] = t["input"]
    t.setdefault("checks", [{"type": "equals"}])
    expr = t.get("expr","")
    try:
        val = eval_expr(expr)
    except Exception as e:
        val = t.get("expected")
    # normalize expected to string if float with .0? keep int as int
    new = val
    if isinstance(val, float):
        new = int(val) if val.is_integer() else val
    if str(t.get("expected")) != str(new):
        t["expected"] = new
        diffs += 1
    fixed.append(t)

out.write_text(json.dumps(fixed, indent=2), encoding="utf-8")
print(str(out))
print("DIFFS", diffs)