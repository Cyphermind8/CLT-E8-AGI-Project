# FILE: tests/test_json_tools_v1.py
from __future__ import annotations
from src.tools.json_tools_v1 import sort_json_values, json_merge

def test_sort_json_values_orders_keys_and_lists():
    obj = {"b": [3, 2, 1], "a": {"y": 2, "x": 1}}
    out = sort_json_values(obj)
    assert list(out.keys()) == ["a", "b"]
    assert out["b"] == [1, 2, 3]
    assert list(out["a"].keys()) == ["x", "y"]

def test_json_merge_combine_mode_unions_lists_and_deep_merges():
    a = {"k": [1, 2], "d": {"x": 1}}
    b = {"k": [2, 3], "d": {"y": 2}}
    out = json_merge(a, b, mode="combine")
    # list union unique, sorted
    assert out["k"] == [1, 2, 3]
    # deep merged dict
    assert out["d"] == {"x": 1, "y": 2}

def test_json_merge_prefer_right_wins_on_conflicts():
    a = {"n": 1, "arr": [1, 2]}
    b = {"n": 9, "arr": [9]}
    out = json_merge(a, b, mode="prefer_right")
    assert out["n"] == 9
    assert out["arr"] == [9]

def test_json_merge_prefer_left_wins_on_conflicts():
    a = {"n": 1, "arr": [1, 2]}
    b = {"n": 9, "arr": [9]}
    out = json_merge(a, b, mode="prefer_left")
    assert out["n"] == 1
    assert out["arr"] == [1, 2]
