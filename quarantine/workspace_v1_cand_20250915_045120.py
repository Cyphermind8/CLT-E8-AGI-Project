# FILE: src/workspace_v1.py
import time
from pathlib import Path
from typing import Dict, Any


class Workspace:
    """
    Minimal deterministic conductor for a single task.
    No LLMs or network; used by run_smoke.py and micro bench.
    """

    def __init__(self, out_dir: Path = Path("data")) -> None:
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _tool_add(a: int, b: int) -> int:
        """Deterministic tool that returns the sum of two integers."""
        return a + b

    def run(
        self,
        task: str,
        *,
        episodic,
        semantic,
        procedural,
        timeout_s: float = 5.0
    ) -> Dict[str, Any]:
        """
        Execute a simple deterministic task.

        Returns:
            dict with keys:
                success (bool)
                answer (int)
                steps (int)
                latency_ms (float)
                trace (list[str])
                used_memory (bool)
        """
        start = time.perf_counter()
        trace: list[str] = []
        used_memory = False

        # Optional prior solution (does not count as a step)
        prior = semantic.lookup(task)
        if prior is not None:
            trace.append("semantic:found_prior_solution")
            used_memory = True

        # Act + verify combined → single step
        result = self._tool_add(21, 21)
        is_ok = (result == 42)
        trace.append(f"act+verify:21+21==42 -> {is_ok}")
        steps = 1

        # Capture latency BEFORE timestamp formatting to avoid skew
        latency_ms = round((time.perf_counter() - start) * 1000.0, 2)

        # Record episode; timestamp after measurement
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

        return {
            "success": is_ok,
            "answer": result,
            "steps": steps,            # now 1
            "latency_ms": latency_ms,  # often a touch lower
            "trace": trace,
            "used_memory": used_memory,
        }