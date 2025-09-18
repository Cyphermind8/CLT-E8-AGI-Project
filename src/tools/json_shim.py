from __future__ import annotations
from .json_tools_v1 import sort_json_values, json_merge

# Backward-compatible names if prompts expect these:
json_sort_values = sort_json_values
json_merge_values = json_merge
