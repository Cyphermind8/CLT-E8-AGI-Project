from ai_core import AICore
from ai_decision import AIDecisionEngine
from ai_learning import AILearning

# propose a tiny safe edit on code_analysis.py (no write)
core = AICore()
mod = core.improve_file("code_analysis.py")
core.record_modification(mod)

# decision ranks by perf_gain (all zeros initially)
AIDecisionEngine().propose_next()

# learning report
AILearning().analyze()
