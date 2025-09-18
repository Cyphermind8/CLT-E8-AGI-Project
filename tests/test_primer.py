# FILE: tests/test_primer.py
#!/usr/bin/env python3
from __future__ import annotations

import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIMER = ROOT / "primer" / "PRIMER.md"

def test_primer_exists_and_fresh():
    assert PRIMER.exists(), "primer/PRIMER.md is missing. Run: python scripts/make_primer.py"
    age_seconds = time.time() - PRIMER.stat().st_mtime
    assert age_seconds <= 24 * 3600, f"PRIMER.md is stale ({age_seconds/3600:.1f}h old). Regenerate: python scripts/make_primer.py"

def test_primer_has_required_sections_and_canary():
    content = PRIMER.read_text(encoding="utf-8")
    assert "## PROJECT SEED (evergreen)" in content, "Missing PROJECT SEED section"
    assert "## RUN SEED (recent deltas)" in content, "Missing RUN SEED section"
    assert "## ASK SEED (fill these before pasting)" in content, "Missing ASK SEED section"
    assert "Canary metric: accepted=" in content and " rate=" in content, "Missing canary metric line"
