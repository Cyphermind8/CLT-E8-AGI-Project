from __future__ import annotations
import os, re, sys, json, subprocess
from typing import Dict, Any, Tuple, Optional

def _last_json(text: str) -> dict:
    m = re.search(r"\{(?:.|\n)*\}\s*$", text.strip())
    if not m:
        raise RuntimeError("Did not find JSON block in stdout.")
    return json.loads(m.group(0))

def run_bench(cwd: str, project_root: Optional[str] = None) -> Tuple[Dict[str, Any], str]:
    """
    Runs your existing bench wrapper and returns (summary_dict, json_report_path).
    Runs inside 'cwd', overriding CLT_E8_PROJECT_ROOT so io_guard points at that cwd.
    """
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    if project_root:
        env["CLT_E8_PROJECT_ROOT"] = project_root
    else:
        env["CLT_E8_PROJECT_ROOT"] = cwd

    # Use the wrapper you already have; it prints a JSON object with "outputs"
    proc = subprocess.run(
        [sys.executable, os.path.join("scripts", "run_bench_with_log.py")],
        cwd=cwd, env=env, text=True, capture_output=True
    )

    out = proc.stdout or ""
    if proc.returncode != 0:
        raise RuntimeError(f"bench failed (rc={proc.returncode}).\nSTDOUT:\n{out}\nSTDERR:\n{proc.stderr}")

    obj = _last_json(out)
    outputs = obj.get("outputs") or {}
    summary = outputs.get("summary")
    json_path = outputs.get("json")
    if not summary or not json_path:
        raise RuntimeError(f"bench json missing keys.\nGot: {json.dumps(obj, indent=2)}")
    return summary, json_path