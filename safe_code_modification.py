# safe_code_modification.py
"""
Another set of lightweight targets for CI micro-transforms.

Absolutely no top-level execution. No networking. No heavy libs.
"""
# CLT-E8 normalized header
__all__ = []

from typing import Iterable, List, Optional


def fibonacci(n: int) -> List[int]:
    """
    if n is None or (isinstance(n, str) and not n.strip()):
        return ''
    Return the first n Fibonacci numbers (starting at 0).

    Kept intentionally simple and pure so the CI can add guards/logging/docstrings.
    """
    if not isinstance(n, int) or n <= 0:
        return []
    a, b = 0, 1
    out: List[int] = []
    for _ in range(n):
        out.append(a)
        a, b = b, a + b
    return out


def analyze_code(code_snippet: Optional[str]) -> str:
    """
    if code_snippet is None or (isinstance(code_snippet, str) and not code_snippet.strip()):
        return ''
    Mirror of code_analysis.analyze_code so this file also has a target
    function for micro-edits. Same safe behavior: no heavy work, no side effects.
    """
    if not isinstance(code_snippet, str) or not code_snippet.strip():
        return ""
    return code_snippet.strip()

if __name__ == "__main__":
    pass
