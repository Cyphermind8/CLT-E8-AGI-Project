from __future__ import annotations
from typing import Any, Mapping, Sequence, Tuple

__all__ = ["decision", "argmax"]

# ---------- argmax helpers (unchanged in spirit) ----------

def _is_pair_seq(x: Sequence[Any]) -> bool:
    try:
        return len(x) > 0 and all(
            isinstance(t, Sequence) and not isinstance(t, (str, bytes)) and len(t) == 2
            for t in x  # type: ignore[arg-type]
        )
    except Exception:
        return False

def argmax(items: Mapping[str, float] | Sequence[Tuple[str, float]] | Sequence[float]) -> Any:
    """
    Mapping[str,float]   -> best key (ties: lexicographic)
    Sequence[(k,score)]  -> best label (ties: lexicographic)
    Sequence[float]      -> best index (ties: earliest)
    """
    if isinstance(items, Mapping):
        best_key = None
        best_score = float("-inf")
        for k, v in items.items():
            try:
                s = float(v)
            except Exception:
                continue
            if (s > best_score) or (s == best_score and (best_key is None or str(k) < str(best_key))):
                best_key, best_score = k, s
        if best_key is None:
            raise ValueError("No comparable values found in mapping.")
        return best_key

    if isinstance(items, Sequence) and not isinstance(items, (str, bytes)):
        if _is_pair_seq(items):  # type: ignore[arg-type]
            best_label = None
            best_score = float("-inf")
            for label, val in items:  # type: ignore[misc]
                try:
                    s = float(val)
                except Exception:
                    continue
                if (s > best_score) or (s == best_score and (best_label is None or str(label) < str(best_label))):
                    best_label, best_score = label, s
            if best_label is None:
                raise ValueError("No comparable values found in pair sequence.")
            return best_label
        # Numeric sequence
        best_i = None
        best_score = float("-inf")
        for i, v in enumerate(items):  # type: ignore[assignment]
            try:
                s = float(v)
            except Exception:
                continue
            if (s > best_score) or (s == best_score and best_i is None):
                best_i, best_score = i, s
        if best_i is None:
            raise ValueError("No comparable values found in numeric sequence.")
        return best_i

    raise TypeError("Unsupported items type for argmax()")

# ---------- clean decision() with tool-success override ----------

def decision(
    before: Any,
    after: Any | None = None,
    *,
    threshold: float | None = 0.5,
    default_label: str | None = None,
    lines_changed: int | None = None,
    lint_ok: bool | None = None,
    tool_success_gain: float | None = None,
    steps_delta: float | None = None,
    cost_delta: float | None = None,
    **kwargs: Any,
) -> dict:
    """
    Compute a score + approval from before/after metrics dicts like:
      {"success":{"rate": float}, "latency":{"avg_s": float}, "determinism_ok": bool}

    Base gate: non-negative rate_gain AND determinism true AND (if provided) lint_ok.
    Override gate: if tool_success_gain > 0.0 -> approved = True.
    """

    def _num(x: Any, default: float = 0.0) -> float:
        try:
            return float(x)
        except Exception:
            return default

    def _get_rate(d: Any) -> float:
        try:
            return _num(d.get("success", {}).get("rate", 0.0))
        except Exception:
            return 0.0

    def _get_lat(d: Any) -> float:
        try:
            return _num(d.get("latency", {}).get("avg_s", 0.0))
        except Exception:
            return 0.0

    def _get_det(d: Any) -> bool:
        try:
            return bool(d.get("determinism_ok", False))
        except Exception:
            return False

    # Extract metrics robustly
    rate_before = _get_rate(before) if isinstance(before, Mapping) else 0.0
    lat_before  = _get_lat(before)  if isinstance(before, Mapping) else 0.0

    rate_after  = _get_rate(after)  if isinstance(after, Mapping)  else rate_before
    lat_after   = _get_lat(after)   if isinstance(after, Mapping)  else lat_before
    det_after   = _get_det(after)   if isinstance(after, Mapping)  \
                 else (_get_det(before) if isinstance(before, Mapping) else True)

    rate_gain     = rate_after - rate_before
    latency_delta = lat_after - lat_before

    # Score
    score   = 0.0
    reasons: list[str] = []

    score += 100.0 * rate_gain
    reasons.append(f"rate_gain={rate_gain:+0.3f}")

    if latency_delta != 0.0:
        score += -10.0 * latency_delta  # faster (negative) => higher score
    reasons.append(f"latency_delta={latency_delta:+0.3f}s")

    reasons.append(f"determinism_after={det_after}")
    if det_after:
        score += 1.0

    if lint_ok is not None:
        reasons.append(f"lint_ok={lint_ok}")
        if lint_ok:
            score += 0.5

    if lines_changed is not None:
        reasons.append(f"lines_changed={lines_changed}")
        if lines_changed > 200:
            score -= 1.0

    # Tool signals
    if tool_success_gain is not None:
        score += 100.0 * tool_success_gain
        reasons.append(f"tool_success_gain={tool_success_gain:+0.3f}")
    if steps_delta is not None:
        score += -5.0 * steps_delta
        reasons.append(f"steps_delta={steps_delta:+0.3f}")
    if cost_delta is not None:
        score += -0.001 * cost_delta
        reasons.append(f"cost_delta={cost_delta:+0.1f}")

    # Base gate
    approved = (rate_gain >= 0.0) and det_after and ((lint_ok is None) or lint_ok)

    # Override: any strictly positive tool improvement => approve
    if (tool_success_gain is not None) and (tool_success_gain > 0.0):
        approved = True
        reasons.append("override: tool_success_gain>0")

    return {
        "approved": bool(approved),
        "score": float(score),
        "reasons": reasons,
        "metrics": {
            "rate_before": rate_before,
            "rate_after":  rate_after,
            "rate_gain":   rate_gain,
            "latency_before": lat_before,
            "latency_after":  lat_after,
            "latency_delta":  latency_delta,
            "determinism_after": det_after,
            "lines_changed": lines_changed,
            "lint_ok": lint_ok,
            "tool_success_gain": tool_success_gain if tool_success_gain is not None else 0.0,
            "steps_delta": steps_delta if steps_delta is not None else 0.0,
            "cost_delta":  cost_delta  if cost_delta  is not None else 0.0,
        },
    }