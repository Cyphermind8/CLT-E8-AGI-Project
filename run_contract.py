# FILE: src/models/run_contract.py
from __future__ import annotations
from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field, field_validator

class RunResult(BaseModel):
    """
    Canonical result contract for workspace_v1.run(...) and similar routines.

    Why this exists:
    - Stops "metric illusions": we always return the same orthogonal fields.
    - Guarantees downstream code/tests can rely on a stable shape.
    - Makes regressions loud (validation error) instead of silent.

    Fields
    ------
    success : bool
        Did the run accomplish the task?
    answer : Union[int, float, str, dict, list, None]
        The final answer/output (task-dependent, optional).
    steps : int
        How many discrete actions/plans/ops were executed.
    latency_ms : float
        Wall-clock time for the run, in milliseconds.
    used_memory : bool
        Whether the run benefitted from prior stored knowledge (semantic/episodic).
    trace : List[str]
        Lightweight breadcrumbs of what happened ("plan:...", "tool:...", "critic:...").
    meta : dict
        Optional extras (e.g., tokens, tool stats). Never required for pass/fail logic.
    """
    success: bool
    answer: Optional[Union[int, float, str, dict, list]] = None
    steps: int = Field(ge=0)
    latency_ms: float = Field(ge=0.0)
    used_memory: bool
    trace: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("trace")
    @classmethod
    def trace_not_too_big(cls, v: List[str]) -> List[str]:
        # Keep traces lightweight; we only need breadcrumbs, not full logs.
        if len(v) > 2000:
            raise ValueError("trace too long; please summarize before returning")
        return v
