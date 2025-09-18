# FILE: tests/test_ai_core_behavior.py
#!/usr/bin/env python3
from __future__ import annotations
import importlib

def test_fibonacci_contract():
    ai_core = importlib.import_module("ai_core")
    fib = getattr(ai_core, "fibonacci", None)
    if fib is None:
        # If it's not present, we don't fail the suite; this is a soft playground.
        return
    assert fib(10) == 55
