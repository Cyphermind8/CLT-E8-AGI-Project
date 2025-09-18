# FILE: scripts/strip_bom.py
"""
Remove a leading UTF-8 BOM (EF BB BF) from files.
Usage:
  python scripts/strip_bom.py                # dry-run, lists files that WOULD change
  python scripts/strip_bom.py --apply        # actually rewrite files in place
  python scripts/strip_bom.py --apply code_analysis.py other.py  # specific files
"""

from __future__ import annotations
import sys, argparse, pathlib

BOM = b"\xEF\xBB\xBF"

def has_bom(p: pathlib.Path) -> bool:
    try:
        with p.open("rb") as f:
            return f.read(3) == BOM
    except FileNotFoundError:
        return False

def strip_bom(p: pathlib.Path) -> bool:
    data = p.read_bytes()
    if data.startswith(BOM):
        p.write_bytes(data[3:])
        return True
    return False

def iter_targets(paths):
    if paths:
        for x in paths:
            p = pathlib.Path(x)
            if p.is_file():
                yield p
    else:
        root = pathlib.Path(".")
        for p in root.rglob("*.py"):
            # Skip virtual envs and quarantine-ish dirs
            if any(part.lower() in {".venv", "venv", "site-packages", "quarantine", "__pycache__"} for part in p.parts):
                continue
            yield p

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--apply", action="store_true", help="Rewrite files to remove leading BOM")
    ap.add_argument("files", nargs="*", help="Optional explicit list of .py files")
    args = ap.parse_args(argv)

    changed = 0
    total = 0
    for p in iter_targets(args.files):
        total += 1
        if has_bom(p):
            if args.apply:
                if strip_bom(p):
                    print(f"[fix] removed BOM: {p}")
                    changed += 1
            else:
                print(f"[would-fix] {p}")
    if not args.apply:
        print(f"[dry-run] files scanned={total} with_bom=listed_above")
    else:
        print(f"[apply] files scanned={total} changed={changed}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
