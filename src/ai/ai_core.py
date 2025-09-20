# FILE: src/ai/ai_core.py
from __future__ import annotations

__all__ = ["fibonacci", "fibonacci_sequence"]

def fibonacci(n: int) -> int:
    """Return the nth Fibonacci number (0-indexed). Raises on invalid input."""
    if not isinstance(n, int):
        raise TypeError("n must be int")
    if n < 0:
        raise ValueError("n must be >= 0")
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a

def fibonacci_sequence(k: int) -> list[int]:
    """Return the first k Fibonacci numbers as a list. Raises on invalid input."""
    if not isinstance(k, int):
        raise TypeError("k must be int")
    if k < 0:
        raise ValueError("k must be >= 0")
    out: list[int] = []
    a, b = 0, 1
    for _ in range(k):
        out.append(a)
        a, b = b, a + b
    return out
