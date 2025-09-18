# FILE: scripts/make_primer.py
#!/usr/bin/env python3
"""
Generate compact, copy-pasteable primers to bootstrap a fresh ChatGPT thread
without dragging the whole prior conversation.

Outputs to ./primer/:
- PROJECT_SEED.md       (evergreen)
- RUN_SEED.md           (recent deltas + canary metric)
- ASK_SEED_TEMPLATE.md  (fill in your current question)
- PRIMER.md             (stitched starter you can paste)

Stdlib-only, robust to missing files.

Canary metric:
- "accepted" is the count of applied==True in the last WINDOW (default 50) modifications
  from ai_performance_log.json; "window" is the number of modifications considered.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

ROOT = Path(__file__).resolve().parents[1]
PRIMER_DIR = ROOT / "primer"
LOG_JSON = ROOT / "ai_performance_log.json"
WINDOW = 50  # last N modifications

PROJECT_SEED = """\
Navigator Primer — CLT-E8
Mode: Default = concise; “Ultrathink” on request.
Machine: Windows + PowerShell; Python 3.10; Local OpenAI-compatible server at http://localhost:1234/v1 (unless specified).
Non-negotiables:
- No async promises. All work is done in-message.
- Prefer small, testable increments + ablations. Always include rollback.
- Provide complete files in one fenced block (# FILE: path). No fragments.
- Run instructions must be Windows-friendly with expected outputs.
- Tests first; metrics logged to ai_performance_log.json.
- Safety gates: preflight (pytest), AST function-set parity, backups to ./backup/, tiny patch budget.
Key artifacts:
- ai_self_modification.py (orchestrator)
- gated_loop.py (micro-transform loop)
- ai_performance_log.json (metrics + modifications)
- scripts/ (tooling)
"""

ASK_SEED_TEMPLATE = """\
Current Ask (fill before starting a new chat):
- Objective:
- Constraints (token/time/tools):
- Inputs to consider (files/paths):
- Decision needed now:
"""

def _load_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _fmt_ts(s: str) -> str:
    # pass through ISO if present; else "n/a"
    if isinstance(s, str) and re.match(r"^\d{4}-\d{2}-\d{2}", s):
        return s
    return "n/a"

def _tail_lines(path: Path, n: int = 60) -> str:
    try:
        data = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        return "\n".join(data[-n:])
    except Exception:
        return ""

def _find_latest_overnight(root: Path) -> Path | None:
    cands = sorted(root.glob("overnight_*.log"), key=lambda p: p.stat().st_mtime)
    return cands[-1] if cands else None

def _summarize_mods(mods: List[Dict[str, Any]], limit: int = 10) -> str:
    if not mods:
        return "No recent modifications logged."
    last = mods[-limit:]
    lines = []
    for m in last:
        ts = _fmt_ts(m.get("timestamp", "n/a"))
        applied = bool(m.get("applied", False))
        target = m.get("target", "n/a")
        cycle = m.get("cycle", "n/a")
        stdout = (m.get("stdout") or "").splitlines()
        outline = stdout[0] if stdout else ""
        if len(outline) > 180:
            outline = outline[:177] + "..."
        lines.append(f"- {ts} | cycle={cycle} | applied={applied} | target={target} | {outline}")
    return "\n".join(lines)

def _canary(mods: List[Dict[str, Any]], window: int = WINDOW) -> tuple[int, int, float]:
    if not mods:
        return 0, 0, 0.0
    last = mods[-window:]
    window_n = len(last)
    accepted = sum(1 for m in last if bool(m.get("applied", False)))
    rate = (accepted / window_n * 100.0) if window_n else 0.0
    return accepted, window_n, rate

def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def main(argv: List[str] | None = None) -> int:
    PRIMER_DIR.mkdir(parents=True, exist_ok=True)

    # Evergreen seed
    _write(PRIMER_DIR / "PROJECT_SEED.md", PROJECT_SEED)

    # Load log and make run seed
    obj = _load_json(LOG_JSON)
    mods = obj.get("modifications", [])
    recent = _summarize_mods(mods, limit=10)
    acc, win, rate = _canary(mods, window=WINDOW)

    run_lines = []
    run_lines.append("Recent Deltas — last modifications")
    run_lines.append(recent or "No recent modifications.")
    run_lines.append("")
    run_lines.append(f"Canary metric: accepted={acc} window={win} rate={rate:.1f}% (last {WINDOW} modifications)")

    latest_overnight = _find_latest_overnight(ROOT)
    if latest_overnight:
        run_lines.append("")
        run_lines.append(f"Overnight log tail ({latest_overnight.name}):")
        run_lines.append("```")
        run_lines.append(_tail_lines(latest_overnight, n=40))
        run_lines.append("```")

    _write(PRIMER_DIR / "RUN_SEED.md", "\n".join(run_lines).strip() + "\n")
    _write(PRIMER_DIR / "ASK_SEED_TEMPLATE.md", ASK_SEED_TEMPLATE)

    stitched = []
    stitched.append("## PROJECT SEED (evergreen)")
    stitched.append((PRIMER_DIR / "PROJECT_SEED.md").read_text(encoding="utf-8"))
    stitched.append("\n## RUN SEED (recent deltas)")
    stitched.append((PRIMER_DIR / "RUN_SEED.md").read_text(encoding="utf-8"))
    stitched.append("\n## ASK SEED (fill these before pasting)")
    stitched.append((PRIMER_DIR / "ASK_SEED_TEMPLATE.md").read_text(encoding="utf-8"))

    _write(PRIMER_DIR / "PRIMER.md", "\n".join(stitched))

    # Short console starter (copy optional)
    print("\n=== New Chat Starter (copy from here) ===\n")
    print((PRIMER_DIR / "PROJECT_SEED.md").read_text(encoding="utf-8"))
    print((PRIMER_DIR / "RUN_SEED.md").read_text(encoding="utf-8"))
    print((PRIMER_DIR / "ASK_SEED_TEMPLATE.md").read_text(encoding="utf-8"))
    print("=== End Starter ===\n")
    print(f"[make_primer] Wrote primer files to: {PRIMER_DIR}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
