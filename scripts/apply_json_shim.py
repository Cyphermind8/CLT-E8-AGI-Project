# FILE: scripts/apply_json_shim.py
"""
Auto-patch bench/*.py to use a tolerant JSON parser.

What it does
------------
- Replaces `json.loads(` with `parse_relaxed(`.
- Inserts `from bench.json_sanitizer import parse_relaxed`
  **after any top-of-file __future__ block** and after the
  module docstring — never before it.
- Makes timestamped backups in ./backup/
- Appends an event to ai_performance_log.json

Run:
    .\.venv\Scripts\Activate
    $env:PYTHONPATH="."
    python scripts\apply_json_shim.py
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
BENCH_DIR = ROOT / "bench"
BACKUP_DIR = ROOT / "backup"

LOADS_RX = re.compile(r"\bjson\s*\.\s*loads\s*\(")
IMPORT_STMT = "from bench.json_sanitizer import parse_relaxed\n"
FUTURE_RX = re.compile(r"^\s*from\s+__future__\s+import\s+(.+)$")

def _find_docstring_end(lines: list[str]) -> int:
    """
    Returns the index *after* the module docstring block if present,
    otherwise 0/1 depending on shebang/encoding header.
    """
    i = 0
    # shebang
    if i < len(lines) and lines[i].startswith("#!"):
        i += 1
    # encoding cookie
    if i < len(lines) and "coding" in lines[i] and "utf" in lines[i].lower():
        i += 1

    if i < len(lines) and lines[i].lstrip().startswith(('"""', "'''")):
        quote = lines[i].lstrip()[:3]
        if lines[i].count(quote) >= 2:
            # single-line docstring
            return i + 1
        i += 1
        while i < len(lines):
            if quote in lines[i]:
                return i + 1
            i += 1
        return i  # unclosed; just return EOF
    return i

def _find_future_block_end(lines: list[str], start: int) -> int:
    i = start
    while i < len(lines):
        if FUTURE_RX.match(lines[i]):
            i += 1
        else:
            break
    return i

def _ensure_import_after_future(text: str) -> str:
    if "from bench.json_sanitizer import parse_relaxed" in text:
        return text
    lines = text.splitlines(keepends=True)

    insert_at = _find_docstring_end(lines)
    insert_at = _find_future_block_end(lines, insert_at)

    lines.insert(insert_at, IMPORT_STMT)
    return "".join(lines)

def _backup(p: Path, ts: str) -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, BACKUP_DIR / f"{p.stem}_{ts}{p.suffix}")

def _apply_to_file(p: Path) -> tuple[int, bool]:
    text = p.read_text(encoding="utf-8")
    new_text, n = LOADS_RX.subn("parse_relaxed(", text)
    if n == 0:
        return 0, False
    new_text = _ensure_import_after_future(new_text)
    p.write_text(new_text, encoding="utf-8")
    return n, True

def _append_perf_log(changed: list[Path], nrep: int, ts: str) -> None:
    import json
    event = {
        "timestamp": ts,
        "event": "apply_json_shim_v2",
        "changed_files": [str(p.relative_to(ROOT)) for p in changed],
        "total_replacements": nrep,
        "note": "JSON loads -> parse_relaxed; import placed after __future__ block.",
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
        print(f"[shim] bench/ not found at {BENCH_DIR}")
        return
    targets = [p for p in BENCH_DIR.rglob("*.py") if p.name != "json_sanitizer.py"]
    if not targets:
        print("[shim] No bench python files found.")
        return
    for p in targets:
        _backup(p, ts)
    changed, total = [], 0
    for p in targets:
        n, ch = _apply_to_file(p)
        total += n
        if ch:
            changed.append(p)
    _append_perf_log(changed, total, ts)
    print(f"[shim] Files changed: {len(changed)}, replacements: {total}")
    for p in changed:
        print("  -", p.relative_to(ROOT))

if __name__ == "__main__":
    main()
