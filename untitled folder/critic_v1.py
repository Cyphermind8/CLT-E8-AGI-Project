"""
critic_v1.py — Tool-grounded verification stubs + Coherence score.
- Verifies arithmetic tasks deterministically.
- Computes a simple Coherence score with components:
  ΔEntropy (proxy via confidence delta), Consistency (self-consistency), Contradictions (normalized).
"""
import math

def verify_math(task, hypothesis):
    """Verify a math task deterministically.
    Task: dict with a, b, c, and op string; Hypothesis: numeric answer (float/int).
    Supported ops: 'fma' (a*b + c), 'mix' ((a+b)*c - a).
    Returns dict with keys: passed (bool), truth (float), error (str if any).
    """
    try:
        a, b, c = task["a"], task["b"], task["c"]
        op = task.get("op", "fma")
        if op == "fma":
            truth = a*b + c
        elif op == "mix":
            truth = (a+b)*c - a
        else:
            truth = a*b + c
        ok = abs(hypothesis - truth) < 1e-6
        return {"passed": ok, "truth": truth}
    except Exception as e:
        return {"passed": False, "error": str(e)}

def coherence_score(d_entropy, consistency, contradictions, w=(1.0, 1.2, 1.5)):
    """Weighted sum for Coherence score."""
    a, b, c = w
    return a*d_entropy + b*consistency - c*contradictions

def normalize01(x, lo, hi):
    """Normalize a value into [0,1]."""
    if hi <= lo: return 0.0
    x = max(lo, min(hi, x))
    return (x - lo) / (hi - lo)
