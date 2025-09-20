# FILE: src/ai_decision.py
from __future__ import annotations
from typing import Any, Mapping, Sequence, Tuple

__all__ = ["decision", "argmax"]

# ------------------------------
# Generic argmax utilities
# ------------------------------
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
    Return the label (for mapping or (label, score) pairs) or index (for numeric sequences)
    corresponding to the maximum score. Ties: lexicographic for labels, earliest index for sequences.
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
        if _is_pair_seq(items):  # sequence of (label, score)
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
        # numeric sequence -> index
        best_i = None
        best_score = float("-inf")
        for i, v in enumerate(items):
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

# ------------------------------
# Eval-aware decision policy
# ------------------------------
def _pull_rate(block: Mapping[str, Any]) -> float | None:
    """Prefer explicit rate; else derive passed/total."""
    try:
        s = block.get("success", {})
        if "rate" in s:
            return float(s["rate"])
        if "passed" in s and "total" in s and s["total"]:
            return float(s["passed"]) / float(s["total"])
    except Exception:
        pass
    return None

def _pull_latency(block: Mapping[str, Any]) -> float | None:
    try:
        lat = block.get("latency", {})
        if "avg_s" in lat:
            return float(lat["avg_s"])
    except Exception:
        pass
    return None

def _pull_det(block: Mapping[str, Any]) -> bool | None:
    v = block.get("determinism_ok")
    if isinstance(v, bool):
        return v
    return None

def decision(
    *args: Any,
    threshold: float | None = 0.5,
    default_label: str | None = None,
    # Eval-policy knobs
    lines_changed: int | None = None,
    lint_ok: bool | None = None,
    min_rate_gain: float = 0.01,
    max_latency_regress: float = 0.00,
    require_determinism: bool = True,
    # Tool metrics (optional deltas)
    tool_success_gain: float | None = None,   # absolute gain in tool success rate (e.g., +0.05)
    steps_delta: float | None = None,         # new_avg_steps - old_avg_steps
    cost_delta: float | None = None           # new_avg_cost_chars - old_avg_cost_chars
) -> Any:
    """
    Two modes:

    1) Eval policy mode: decision(before, after, ...[, tool_success_gain, steps_delta, cost_delta])
       Approves if:
         - rate_gain >= min_rate_gain (+ small extra if lines_changed > 50)
         - latency does not regress (or is missing/NA)
         - determinism OK (if required)
         - lint_ok True (default True if unspecified)
         - If tool deltas provided: tool_success_gain >= 0 and (steps_delta <= 0 or cost_delta <= 0)

       Returns a dict with 'approved', 'score', 'reasons', 'metrics'.

    2) Generic mode (back-compat):
       decision(x) where x is number/bool -> thresholded bool
       decision(mapping/sequence) -> argmax label or index
    """
    # ---------- Eval policy mode ----------
    if len(args) >= 2 and all(isinstance(a, Mapping) for a in args[:2]):
        before: Mapping[str, Any] = args[0]  # type: ignore[assignment]
        after:  Mapping[str, Any] = args[1]  # type: ignore[assignment]

        r0 = _pull_rate(before); r1 = _pull_rate(after)
        l0 = _pull_latency(before); l1 = _pull_latency(after)
        det_after = _pull_det(after)

        rate_gain = (r1 - r0) if (r0 is not None and r1 is not None) else None
        lat_delta = (l1 - l0) if (l0 is not None and l1 is not None) else None  # negative is faster

        # defaults and small-risk scaling
        if lint_ok is None:
            lint_ok = True
        extra_gain = 0.005 if (isinstance(lines_changed, int) and lines_changed > 50) else 0.0

        ok_rate = (rate_gain is not None) and (rate_gain >= (min_rate_gain + extra_gain))
        ok_lat  = (lat_delta is None) or (lat_delta <= max_latency_regress)
        ok_det  = (not require_determinism) or (det_after is True)
        ok_lint = (lint_ok is True)

        # Tool gate (only if provided)
        if tool_success_gain is not None or steps_delta is not None or cost_delta is not None:
            ok_tool = True
            if tool_success_gain is not None and tool_success_gain < 0.0:
                ok_tool = False
            if steps_delta is not None and cost_delta is not None:
                if steps_delta > 0.0 and cost_delta > 0.0:
                    ok_tool = False
            elif steps_delta is not None:
                if steps_delta > 0.0: ok_tool = False
            elif cost_delta is not None:
                if cost_delta > 0.0: ok_tool = False
        else:
            ok_tool = True

        approved = ok_rate and ok_lat and ok_det and ok_lint and ok_tool

        # ---- Score (monotonic, human-scaled) ----
        score = 0.0
        if rate_gain is not None: score += 100.0 * rate_gain            # +8 for +0.08
        if lat_delta is not None: score += -10.0 * lat_delta            # faster (negative) => positive points
        if det_after is True:     score += 1.0
        elif det_after is False:  score -= 1.0
        if lint_ok is True:       score += 0.5
        elif lint_ok is False:    score -= 2.0
        if isinstance(lines_changed, int) and lines_changed > 50:
            score -= 0.01 * (lines_changed - 50)

        # tool deltas
        if tool_success_gain is not None: score += 100.0 * tool_success_gain
        if steps_delta is not None:       score += -5.0 * steps_delta
        if cost_delta is not None:        score += -0.001 * cost_delta

        # reasons
        reasons: list[str] = []
        reasons.append(f"rate_gain={'NA' if rate_gain is None else f'{rate_gain:.3f}'}")
        reasons.append("latency=NA" if lat_delta is None else f"latency_delta={lat_delta:+.3f}s")
        if det_after is not None: reasons.append(f"determinism_after={det_after}")
        reasons.append(f"lint_ok={lint_ok}")
        if isinstance(lines_changed, int): reasons.append(f"lines_changed={lines_changed}")
        if tool_success_gain is not None: reasons.append(f"tool_success_gain={tool_success_gain:+.3f}")
        if steps_delta is not None:       reasons.append(f"steps_delta={steps_delta:+.3f}")
        if cost_delta is not None:        reasons.append(f"cost_delta={cost_delta:+.1f}")

        return {
            "approved": approved,
            "score": score,
            "reasons": reasons,
            "metrics": {
                "rate_before": r0, "rate_after": r1, "rate_gain": rate_gain,
                "latency_before": l0, "latency_after": l1, "latency_delta": lat_delta,
                "determinism_after": det_after,
                "lines_changed": lines_changed, "lint_ok": lint_ok,
                "tool_success_gain": tool_success_gain,
                "steps_delta": steps_delta, "cost_delta": cost_delta,
            },
        }

    # ---------- Generic mode (back-compat) ----------
    if len(args) == 1:
        x = args[0]
        if isinstance(x, (int, float, bool)):
            if threshold is None:
                return bool(x)
            try:
                return float(x) >= float(threshold)
            except Exception:
                return bool(x)
        if isinstance(x, Mapping):
            return argmax(x)
        if isinstance(x, Sequence) and not isinstance(x, (str, bytes)):
            if _is_pair_seq(x):
                return argmax(x)
            return argmax(x)
        raise TypeError(f"Unsupported input type for decision(): {type(x).__name__}")

    raise TypeError("decision(): unsupported argument pattern")