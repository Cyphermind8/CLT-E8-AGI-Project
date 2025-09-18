# FILE: ai_self_modification.py
#!/usr/bin/env python3
"""
CLT–E8 Safe Self-Modification Orchestrator (Zero-Defect compliant)

- Runs gated micro-edits in-process via gated_loop.main(argv).
- Runs pytest preflight unless --no-preflight is passed.
- Logs every cycle to ai_performance_log.json.
- CPU-only, deterministic; never writes outside gated_loop's target.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Tuple

import gated_loop  # local import


LOG_PATH = Path("ai_performance_log.json")
ALLOWLIST = {
    Path("code_analysis.py"),
    Path("eval_loop.py"),
    Path("safe_code_modification.py"),
    Path("ai_core.py"),
}


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"modifications": []}
    try:
        return json.loads(path.read_text(encoding="utf-8") or "{}")
    except Exception:
        ts = time.strftime("%Y%m%d_%H%M%S")
        q = Path("backup") / f"ai_performance_log_corrupt_{ts}.json"
        q.parent.mkdir(parents=True, exist_ok=True)
        try:
            q.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        except Exception:
            pass
        return {"modifications": []}


def _save_json(path: Path, obj: Dict[str, Any]) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_log(entry: Dict[str, Any]) -> None:
    log = _load_json(LOG_PATH)
    log.setdefault("modifications", []).append(entry)
    _save_json(LOG_PATH, log)


def _run_preflight() -> None:
    try:
        import pytest  # type: ignore
    except Exception:
        raise SystemExit("Preflight requires pytest. Install it in your venv (pip install -U pytest).")
    rc = pytest.main(["-q"])
    if rc != 0:
        raise SystemExit(f"Preflight tests failed (pytest rc={rc}). Aborting self-modification.")


def _cycle_once(cycle_idx: int, strict: bool, target_path: str = "") -> Tuple[bool, str]:
    argv: List[str] = ["--cycle", str(cycle_idx)]
    if strict:
        argv.append("--strict")
    if target_path:
        argv.extend(["--path", target_path])

    out = StringIO()
    real_stdout = sys.stdout
    t0 = time.time()
    try:
        sys.stdout = out
        exit_code = gated_loop.main(argv)
    finally:
        sys.stdout = real_stdout
    elapsed = time.time() - t0
    text = out.getvalue()
    applied = "[+] Applied:" in text
    return applied, text + f"\n[orchestrator] elapsed={elapsed:.3f}s exit={exit_code}\n"


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safe self-mod orchestrator")
    parser.add_argument("--cycles", type=int, default=3, help="Number of cycles to run (default 3)")
    parser.add_argument("--strict", action="store_true", help="Pass --strict to gated_loop")
    parser.add_argument("--no-preflight", action="store_true", help="Skip pytest preflight (not recommended)")
    parser.add_argument("--path", default="", help="Explicit target file path (optional)")
    args = parser.parse_args(argv or [])

    # Environment overrides (one-way: they can only strengthen)
    env_cycles = os.getenv("CYCLES")
    if env_cycles and env_cycles.isdigit():
        args.cycles = int(env_cycles)
    if os.getenv("STRICT") == "1":
        args.strict = True  # never force False

    if args.path and Path(args.path) not in ALLOWLIST:
        print(f"[orchestrator] WARNING: target {args.path} not in allowlist {sorted(map(str, ALLOWLIST))}")

    if not args.no_preflight:
        print("[orchestrator] Running preflight (pytest -q)...")
        _run_preflight()
        print("[orchestrator] Preflight OK.")

    print(f"[orchestrator] Starting cycles={args.cycles} strict={args.strict} path={args.path or '(rotating)'}")
    session_start = datetime.utcnow().isoformat() + "Z"

    applied_total = 0
    for c in range(args.cycles):
        applied, stdout_text = _cycle_once(c, args.strict, args.path)
        applied_total += 1 if applied else 0
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "cycle": c,
            "strict": args.strict,
            "target": args.path or "rotating candidates",
            "applied": applied,
            "stdout": stdout_text.strip()[:4000],
        }
        _append_log(entry)
        print(f"[orchestrator] cycle={c} applied={applied}")

    print(f"[orchestrator] done. session_start={session_start} applied_total={applied_total}/{args.cycles}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
