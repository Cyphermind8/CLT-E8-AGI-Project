# FILE: src/utils/extract_blocks.py
import re
from typing import List, Tuple

# Fenced form:
# ```python
# # FILE: src/workspace_v1.py
# <code>
# ```
FENCE_RE = re.compile(
    r"```(?:[a-zA-Z0-9_+\-]*\n)?(#\s*FILE:\s*(?P<path>[^\r\n]+)\r?\n)(?P<body>.*?)(?:```|\Z)",
    re.DOTALL,
)

# Unfenced form:
# # FILE: src/workspace_v1.py
# <code>
UNFENCED_RE = re.compile(
    r"(^|\n)#\s*FILE:\s*(?P<path>[^\r\n]+)\r?\n(?P<body>.*?)(?=\n#\s*FILE:|\Z)",
    re.DOTALL,
)

def _normalize_path(p: str) -> str:
    # Keep Windows-friendly, but collapse doubles
    return p.strip().replace("/", "\\").replace("\\\\", "\\")

def extract_file_blocks(text: str) -> List[Tuple[str, str]]:
    """
    Parse an LLM reply and return [(relative_path, file_body), ...].
    Prefers fenced blocks; falls back to unfenced # FILE: blocks.
    """
    blocks: List[Tuple[str, str]] = []

    # 1) Prefer fenced
    for m in FENCE_RE.finditer(text):
        path = _normalize_path(m.group("path"))
        body = m.group("body").rstrip("`").rstrip()
        blocks.append((path, body))

    # 2) If none fenced, accept unfenced
    if not blocks:
        for m in UNFENCED_RE.finditer(text):
            path = _normalize_path(m.group("path"))
            body = m.group("body").rstrip()
            blocks.append((path, body))

    return blocks
