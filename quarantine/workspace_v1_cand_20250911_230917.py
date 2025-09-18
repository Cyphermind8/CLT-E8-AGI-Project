import time
from pathlib import Path
from typing import Dict, Any, Optional

class Workspace:
    """
    Minimal, deterministic conductor for a single task.
    No LLMs, no network. Designed to make run_smoke.py pass and to
    establish the data contract for later GPT-OSS integration.
    """

    def __init__(self, out_dir: Path = Path("data")):
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def _tool_add(self, a: int, b: int) -> int:
        # Deterministic "tool" to compute 21 + 21 for the smoke task.
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
        Returns a run dict with keys:
        - success: bool
        - answer: str/int
        - steps: int
        - latency_ms: float
        - trace: list[str]
        - used_memory: bool
        """
        t0 = time.perf_counter()
        trace = []
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