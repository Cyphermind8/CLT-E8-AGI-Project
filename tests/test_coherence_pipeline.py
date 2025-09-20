from pathlib import Path
from src.ai.ai_learning import LearningState
from src.ai.ai_decision import make_plan

def test_make_plan_from_min_state(tmp_path: Path):
    st = LearningState(pass_rate=0.8, determinism_ok=True, avg_latency_s=3.2,
                       failed_cases=["json_merge"], notes=["coherence~=0.75"],
                       opportunities=[{"kind":"tool_dispatch_arg_mapping","test":"json_sort_values","target_file":"src/tools/json_tools_v1.py"}])
    plan = make_plan(st)
    assert plan.actions, "should propose at least one action"
    assert any(a.get("type") == "rerun_bench" for a in plan.actions)
