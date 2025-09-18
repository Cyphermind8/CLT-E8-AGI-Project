# FILE: src/tools/json_tools.py
```python
"""
Utility functions for JSON manipulation.
"""

import json
from typing import Any, Dict

def load_json(file_path: str) -> Dict[str, Any]:
    """
    Load a JSON file and return its contents as a dictionary.

    Parameters:
        file_path (str): Path to the JSON file.

    Returns:
        dict: Parsed JSON data.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def dump_json(data: Dict[str, Any], file_path: str) -> None:
    """
    Dump a dictionary to a JSON file.

    Parameters:
        data (dict): Data to serialize.
        file_path (str): Destination file path.
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
```