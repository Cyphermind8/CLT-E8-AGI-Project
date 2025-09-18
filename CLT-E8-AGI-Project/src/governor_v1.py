"""
governor_v1.py — Minimal rails: sandboxing, allowlist, logging stubs.
"""
def allow(action: str) -> bool:
    return action in {"calc", "pyexec", "fileio"}
