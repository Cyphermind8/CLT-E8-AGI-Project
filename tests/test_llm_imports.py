# FILE: tests/test_llm_imports.py
"""
This test ensures LLM helper modules import and expose callable entry points
without attempting any network calls (we do not call GPT-OSS here).
"""

def test_llm_helpers_import_and_shapes():
    from src.llm.planner_llm import suggest_plan
    from src.llm.critic_llm import verify_result

    # Should be callable
    assert callable(suggest_plan)
    assert callable(verify_result)

    # With LLM disabled (default), planner returns deterministic fallback
    plan = suggest_plan("Compute 21 + 21 using available tools, verify, and record the method.")
    assert isinstance(plan, list) and len(plan) >= 1
    step = plan[0]
    assert isinstance(step, dict) and "action" in step

    verdict = verify_result("Compute 21 + 21 using available tools, verify, and record the method.", 42)
    assert isinstance(verdict, dict) and "ok" in verdict
    assert verdict["ok"] is True
