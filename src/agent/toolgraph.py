# FILE: src/agent/toolgraph.py
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json, time
from typing import Any, Dict

from src.tools.retrieval import MiniLexicalIndex
from src.tools.calculator import eval_expr
from src.tools.code_exec import run as run_code

LOGS = Path(__file__).resolve().parents[2] / "logs"
KB   = Path(__file__).resolve().parents[2] / "data" / "knowledge"
LOGS.mkdir(parents=True, exist_ok=True)

def log_tool(runlog: Path, name: str, ok: bool, start: float, end: float, **extra: Any) -> None:
    rec = {"ts": time.time(), "tool": name, "ok": bool(ok), "dt": round(end-start, 6)}
    rec.update(extra)
    runlog.write_text((runlog.read_text(encoding="utf-8") if runlog.exists() else "") + json.dumps(rec)+"\n", encoding="utf-8")

@dataclass
class Variant:
    name: str
    planner: str         # "react" | "plan" (placeholder for now)
    verify:  str         # "equals" | "contains" | "none"

class ToolGraph:
    def __init__(self, variant: Variant):
        self.variant = variant
        self.index = MiniLexicalIndex(KB)

    def run_task(self, task: Dict[str, Any], runlog: Path) -> tuple[bool,int,int]:
        steps = 0
        est_cost = 0
        typ = task.get("type") or task.get("task_type") or "calc"

        def est(s: str) -> int:  # chars/4 ≈ tokens
            return max(1, len(s)//4)

        if typ == "math":
            t0=time.time()
            try:
                val = eval_expr(task["expr"])
                ok = (val == task["expected"])
            except Exception:
                ok = False
            t1=time.time()
            steps+=1; est_cost+=est(task["expr"])
            log_tool(runlog, "calculator", ok, t0, t1, expr=task["expr"])
            return ok, steps, est_cost

        if typ == "code":
            t0=time.time()
            try:
                val = run_code(task["code"])
                ok = (val == task["expected"])
            except Exception:
                ok=False
            t1=time.time()
            steps+=1; est_cost+=est(task["code"])
            log_tool(runlog, "code_exec", ok, t0, t1)
            return ok, steps, est_cost

        if typ == "retrieve":
            q = task["question"]
            t0=time.time(); hits = self.index.search(q, k=1); t1=time.time()
            ok = False
            if hits:
                path,score,txt = hits[0]
                ok = (task["must_contain"].lower() in txt.lower())
            steps+=1; est_cost+=est(q)
            log_tool(runlog, "retrieve", ok, t0, t1, q=q)
            return ok, steps, est_cost

        if typ == "pipeline":
            ok=True
            for step in task["plan"]:
                if step["tool"]=="retrieve":
                    q=step["query"]; t0=time.time(); hits=self.index.search(q,k=1); t1=time.time()
                    this_ok=bool(hits)
                    steps+=1; est_cost+=est(q)
                    log_tool(runlog, "retrieve", this_ok, t0, t1, q=q)
                    ok = ok and this_ok
                elif step["tool"]=="compute":
                    code=step["code"]; t0=time.time()
                    try: val=run_code(code); this_ok=True
                    except Exception: this_ok=False; val=None
                    t1=time.time()
                    steps+=1; est_cost+=est(code)
                    log_tool(runlog, "code_exec", this_ok, t0, t1)
                    ok = ok and this_ok
            # verify
            ver = task.get("verify", {"type":"none"})
            vtype = ver.get("type","none")
            v_ok=True
            if vtype=="equals": v_ok = (val == ver.get("value"))
            elif vtype=="contains": v_ok = isinstance(val,str) and (ver.get("value","").lower() in val.lower())
            ok = ok and v_ok
            return ok, steps, est_cost

        return False, steps, est_cost