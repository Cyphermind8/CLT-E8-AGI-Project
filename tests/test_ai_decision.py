from src.ai_decision import decision

def test_decision_basic():
    before = {"success": {"passed": 9, "total": 12, "rate": 0.75},
              "determinism_ok": False,
              "latency": {"avg_s": 3.6}}
    after  = {"success": {"passed": 10, "total": 12, "rate": 0.83},
              "determinism_ok": True,
              "latency": {"avg_s": 3.4}}
    rep = decision(before, after, lines_changed=8, lint_ok=True)
    assert rep["score"] > 0
