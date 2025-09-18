# FILE: scripts/preflight.py
#!/usr/bin/env python3
"""
Preflight gate for CLT–E8 AI_Project.

Runs pytest quietly and exits non-zero on any failure.
This script is intentionally tiny and dependency-light.
"""

from __future__ import annotations

import sys

def main() -> int:
    try:
        import pytest  # type: ignore
    except Exception:
        print("Preflight requires pytest. Install it: pip install -U pytest", file=sys.stderr)
        return 2
    rc = pytest.main(["-q"])
    if rc != 0:
        print(f"[preflight] pytest failed (rc={rc}).", file=sys.stderr)
    else:
        print("[preflight] OK")
    return int(rc != 0)

if __name__ == "__main__":
    raise SystemExit(main())
