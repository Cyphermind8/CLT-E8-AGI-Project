from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple

# CLT-E8 coherence vector with 8 axes in [0,1]
# 1 Accuracy / Truthfulness          (bench pass rate)
# 2 Determinism / Repeatability      (bench determinism flag)
# 3 Efficiency / Parsimony           (latency improvements)
# 4 Simplicity / Minimality          (lines changed, smaller is better)
# 5 Safety / Guardedness             (Governor writes only; assume safe unless signaled)
# 6 Generality / Breadth             (task coverage; proxy = total tasks > 0)
# 7 Robustness / Stability           (CI/pytest pass %; if unknown, neutral)
# 8 Internal Coherence               (no contradictions among metrics; here a simple proxy)

AXES = [
    "accuracy", "determinism", "efficiency", "simplicity",
    "safety", "generality", "robustness", "internal"
]

@dataclass(frozen=True)
class CoherenceVec:
    accuracy: float
    determinism: float
    efficiency: float
    simplicity: float
    safety: float
    generality: float
    robustness: float
    internal: float

    def as_dict(self) -> Dict[str, float]:
        return {k: getattr(self, k) for k in AXES}

def _clamp01(x: float) -> float:
    return 0.0 if x < 0 else 1.0 if x > 1 else x

def _safe_ratio(num: float, den: float) -> float:
    if den <= 0: return 0.0
    return _clamp01(num / den)

def assess_run(summary: Dict[str, Any]) -> CoherenceVec:
    """Map a bench/summary (like your reports JSON) to a CLT-E8 vector."""
    # Expected shape from your bench:
    # summary["success"]["passed"], summary["success"]["total"], summary["success"]["rate"]
    # summary["determinism_ok"] (bool)
    # summary["latency"]["avg_s"]
    passed = float(summary.get("success", {}).get("passed", 0))
    total  = float(summary.get("success", {}).get("total", 0))
    rate   = float(summary.get("success", {}).get("rate", _safe_ratio(passed, total)))
    determinism_ok = bool(summary.get("determinism_ok", False))

    # Latency: lower is better. Normalize against a soft target (3s).
    avg_lat = float(summary.get("latency", {}).get("avg_s", 3.0))
    efficiency = _clamp01(3.0 / max(avg_lat, 1e-6))  # ~1 near 3s, >1 capped

    # Generality proxy: tasks available and attempted
    generality = 1.0 if total >= 12 else _clamp01(total / 12.0)

    # Robustness proxy: if pytest pass rate known in caller extras, otherwise neutral 0.5
    robustness = float(summary.get("_pytest_pass_rate", 0.5))

    # Safety: default 1.0 unless caller flags any guard violations
    safety = 1.0 if not summary.get("_guard_violations") else 0.0

    # Simplicity: filled by decision() from candidate metadata; neutral here
    simplicity = 0.5

    # Internal coherence: if rate high & determinism ok, boost; if they contradict, reduce
    internal = 0.8
    if rate >= 0.9 and determinism_ok:
        internal = 1.0
    elif rate < 0.5 and determinism_ok:
        internal = 0.6
    elif rate >= 0.9 and not determinism_ok:
        internal = 0.6

    return CoherenceVec(
        accuracy=_clamp01(rate),
        determinism=1.0 if determinism_ok else 0.2,
        efficiency=efficiency,
        simplicity=simplicity,
        safety=safety,
        generality=generality,
        robustness=robustness,
        internal=internal,
    )

def combine(before: CoherenceVec, after: CoherenceVec, simplicity_bonus: float) -> Tuple[float, Dict[str, float]]:
    """Weighted sum with a readable per-axis breakdown."""
    w = {
        "accuracy":     0.30,
        "determinism":  0.15,
        "efficiency":   0.15,
        "simplicity":   0.10,
        "safety":       0.10,
        "generality":   0.05,
        "robustness":   0.10,
        "internal":     0.05,
    }
    axes_delta = {}
    score = 0.0
    for k in AXES:
        b = getattr(before, k)
        a = getattr(after,  k)
        d = a - b
        if k == "simplicity":
            # "simplicity_bonus" comes from the candidate (smaller patch = higher bonus)
            d = simplicity_bonus - (b - 0.5)  # center around 0.5 baseline
        axes_delta[k] = d
        score += w[k] * d
    return score, axes_delta

def decision(before_summary: Dict[str, Any],
             after_summary: Dict[str, Any],
             *,
             lines_changed: Optional[int] = None,
             lint_ok: Optional[bool] = None) -> Dict[str, Any]:
    """Return a decision report with total score and per-axis deltas."""
    b = assess_run(before_summary)
    a = assess_run(after_summary)

    # Simplicity bonus: 1.0 for tiny patches, ~0.6 moderate, ≤0.5 large
    if lines_changed is None:
        simplicity_bonus = 0.5
    else:
        if lines_changed <= 10:   simplicity_bonus = 1.0
        elif lines_changed <= 30: simplicity_bonus = 0.8
        elif lines_changed <= 80: simplicity_bonus = 0.6
        else:                     simplicity_bonus = 0.5

    # Lint/format OK nudges simplicity slightly up
    if lint_ok:
        simplicity_bonus = min(1.0, simplicity_bonus + 0.05)

    score, axes_delta = combine(b, a, simplicity_bonus)
    return {
        "score": round(float(score), 6),
        "simplicity_bonus": round(float(simplicity_bonus), 3),
        "axes_delta": {k: round(v, 6) for k, v in axes_delta.items()},
        "before": b.as_dict(),
        "after":  a.as_dict(),
    }
