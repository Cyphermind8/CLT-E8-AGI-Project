# FILE: scripts/fix_future_imports.py
"""
Normalize `from __future__ import ...` placement in bench/*.py

- Collects any number of scattered future-import lines.
- Deduplicates & sorts features.
- Inserts a single combined future-import line right after the
  module docstring (and shebang/encoding, if present).
- Removes the old scattered lines.
- Backups to ./backup/ and logs an event.

Run:
    .\.venv\Scripts\Activate
    $env:PYTHONPATH="."
    python scripts\fix_future_imports.py
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
BENCH_DIR = ROOT / "bench"
BACKUP_DIR = ROOT / "backup"

FUTURE_RX = re.compile(r"^\s*from\s+__future__\s+import\s+(.+)$")

def _find_docstring_end(lines: list[str]) -> int:
    i = 0
    if i < len(lines) and lines[i].startswith("#!"):
        i += 1
    if i < len(lines) and "coding" in lines[i] and "utf" in lines[i].lower():
        i += 1
    if i < len(lines) and lines[i].lstrip().startswith(('"""', "'''")):
        quote = lines[i].lstrip()[:3]
        if lines[i].count(quote) >= 2:
            return i + 1
        i += 1
        while i < len(lines):
            if quote in lines[i]:
                return i + 1
            i += 1
        return i
    return i

def _backup(p: Path, ts: str) -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, BACKUP_DIR / f"{p.stem}_{ts}{p.suffix}")

def _normalize_file(p: Path) -> bool:
    text = p.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    # collect future imports
    features: list[str] = []
    to_delete: list[int] = []
    for i, line in enumerate(lines):
        m = FUTURE_RX.match(line)
        if m:
            parts = [f.strip() for f in m.group(1).split(",")]
            features.extend([x for x in parts if x])
            to_delete.append(i)

    if not features:
        return False

    # remove old lines
    for idx in reversed(to_delete):
        lines.pop(idx)

    # compute insert point & new line
    insert_at = _find_docstring_end(lines)
    future_line = "from __future__ import " + ", ".join(sorted(set(features))) + "\n"

    # If an identical future import already exists at the right place, skip
    # (after removals). Otherwise, insert.
    already_ok = False
    if insert_at < len(lines) and lines[insert_at].strip() == future_line.strip():
        already_ok = True

    if not already_ok:
        lines.insert(insert_at, future_line)

    p.write_text("".join(lines), encoding="utf-8")
    return True

def _append_perf_log(changed: list[Path], ts: str) -> None:
    import json
    event = {
        "timestamp": ts,
        "event": "fix_future_imports",
        "changed_files": [str(p.relative_to(ROOT)) for p in changed],
        "note": "Consolidated and re-positioned __future__ imports to the top.",
    }
    log = ROOT / "ai_performance_log.json"
    try:
        payload = []
        if log.exists():
            existing = json.loads(log.read_text(encoding="utf-8"))
            if isinstance(existing, list):
                payload = existing
            else:
                payload = [existing]
        payload.append(event)
        log.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except Exception:
        pass

def main() -> None:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    if not BENCH_DIR.exists():
        print(f"[future-fix] bench/ not found at {BENCH_DIR}")
        return
    targets = list(BENCH_DIR.rglob("*.py"))
    if not targets:
        print("[future-fix] No bench python files found.")
        return

    changed: list[Path] = []
    for p in targets:
        _backup(p, ts)
        if _normalize_file(p):
            changed.append(p)

    _append_perf_log(changed, ts)
    print(f"[future-fix] Files changed: {len(changed)}")
    for p in changed:
        print("  -", p.relative_to(ROOT))

if __name__ == "__main__":
    main()
