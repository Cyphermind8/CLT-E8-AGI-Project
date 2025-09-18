# FILE: tests/test_code_analysis_behavior.py
"""
Behavior contract tests for code_analysis.analyze_code().

Purpose: keep the function simple, deterministic, and CI-safe.
If these tests fail, the gated loop should be blocked before mutating files.
"""

from __future__ import annotations

import importlib
import types


def test_import_and_callable():
    mod = importlib.import_module("code_analysis")
    assert isinstance(mod, types.ModuleType)
    assert hasattr(mod, "analyze_code")
    assert callable(mod.analyze_code)


def test_returns_empty_on_none_or_blank():
    from code_analysis import analyze_code
    assert analyze_code(None) == ""
    assert analyze_code("") == ""
    assert analyze_code("   ") == ""


def test_trims_strings_and_echoes():
    from code_analysis import analyze_code
    assert analyze_code(" hello ") == "hello"
    assert analyze_code("\n\tfoo\t\n") == "foo"


def test_non_string_non_none_inputs():
    from code_analysis import analyze_code
    # Anything not a string should return empty (conservative behavior)
    assert analyze_code(123) == ""
    assert analyze_code({"k": "v"}) == ""
    assert analyze_code(["a", "b"]) == ""
