# Minimal shim: prefer the maintained core under src/, no raw writes here.
try:
    from src.ai.ai_core import *  # re-export maintained APIs
except Exception as e:
    # keep import error explicit for debugging
    raise
