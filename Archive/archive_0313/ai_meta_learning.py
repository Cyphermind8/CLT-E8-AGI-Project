import json
from datetime import datetime
from ai_memory import ai_memory
from ai_optimization import ai_optimization

class AIMetaLearning:
    def __init__(self):
        self.memory = ai_memory
        self.optimization = ai_optimization

    def assess_learning_efficiency(self):
        """Evaluates AI's past self-improvements to determine if learning is accelerating or stagnating."""
        modifications = self.memory.get_last_n_modifications(n=10)

        if not modifications:
            return "No modifications available for assessment."

        success_rate = sum(1 for mod in modifications if "AI Applied Modification" in mod["event"]) / len(modifications)
        entropy_scaling = sum(mod["entropy_score"] for mod in modifications) / len(modifications)

        return {
            "success_rate": round(success_rate * 100, 2),
            "entropy_scaling": round(entropy_scaling, 2),
            "trend": "Improving" if entropy_scaling > 0.6 else "Needs Refinement"
        }

    def refine_learning_process(self):
        """AI dynamically adjusts how it self-improves based on past learning trends."""
        assessment = self.assess_learning_efficiency()
        if isinstance(assessment, str):  # No data available
            return "AI requires more modifications before refining its learning process."

        if assessment["trend"] == "Improving":
            print("🚀 AI Meta-Learning: Learning process is effective. Continuing optimization.")
        else:
            print("⚠️ AI Meta-Learning: Adjusting improvement cycles to refine learning.")
            self.optimization.discard_low_quality_modifications()

# ✅ Initialize AI Meta-Learning System
ai_meta_learning = AIMetaLearning()
