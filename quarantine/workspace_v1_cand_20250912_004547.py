# FILE: src/workspace_v1.py
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

class Workspace:
    """
    Minimal, deterministic conductor for a single task.
    No LLMs, no network. Designed to make run_smoke.py pass and to
    establish the data contract for later GPT-OSS integration.
    """

    def __init__(self, out_dir: Path = Path("data")) -> None:
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def _tool_add(self, a: int, b: int) -> int:
        # Deterministic "tool" to compute 21 + 21 for the smoke task.
        return a + b

    def run(
        self,
        task: str,
        *,
        episodic: List[Dict[str, Any]],
        semantic: Any,
        procedural: Any,
        timeout_s: float = 5.0
    ) -> Dict[str, Any]:
        """
        Execute a single deterministic task.

        Parameters
        ----------
        task : str
            Identifier of the task to run.
        episodic : list[dict]
            List where episode records are appended.
        semantic : object
            Object providing ``lookup`` and ``remember`` methods for memory.
        procedural : object
            Placeholder for future procedural logic (unused here).
        timeout_s : float, optional
            Maximum allowed time in seconds (currently unused).

        Returns
        -------
        dict
            Dictionary containing execution metadata:
                - success: bool
                - answer: int | None
                - steps: int
                - latency_ms: float
                - trace: list[str]
                - used_memory: bool
        """
        t0 = time.perf_counter()
        trace: List[str] = []
        steps = 0
        used_memory = False
        answer: Optional[int] = None

        # 1) Retrieve prior hints from memory (semantic)
        prior = semantic.lookup(task)
        if prior is not None:
            trace.append("semantic:found_prior_solution")
            used_memory = True

        # 2) Plan (trivial for now)
        trace.append("plan:compute_21_plus_21")
        steps += 1

        # 3) Act with the deterministic tool
        steps += 1
        result = self._tool_add(21, 21)
        trace.append("tool_add:21+21")

        # 4) Verify (critic = simple equality check)
        steps += 1
        is_ok = (result == 42)
        trace.append(f"critic:check==42 -> {is_ok}")

        # 5) Write episode + semantic fact
        steps += 1
        episode = {
            "task": task,
            "result": result,
            "success": is_ok,
            "trace": trace,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        episodic.append(episode)
        if is_ok:
            semantic.remember(task, {"method": "tool_add", "a": 21, "b": 21, "result": 42})

        answer = result
        latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        return {
            "success": bool(is_ok),
            "answer": answer,
            "steps": steps,
            "latency_ms": latency_ms,
            "trace": trace,
            "used_memory": used_memory,
        }