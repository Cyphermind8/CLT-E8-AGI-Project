import json
from datetime import datetime
from ai_memory import ai_memory

class AIDecisionEngine:
    def __init__(self):
        self.memory = ai_memory

    def evaluate_modification_success(self, modification):
        """Check if a past modification improved AI intelligence."""
        past_modifications = self.memory.get_last_n_modifications(n=10)
        for past_mod in past_modifications:
            if modification in past_mod["details"]:
                return past_mod["entropy_score"] > 0.6  # Only keep high-impact changes
        return False

    def select_best_modification(self):
        """Choose the highest-ranked improvement from memory."""
        best_modifications = self.memory.get_highest_entropy_modifications(n=5)
        if best_modifications:
            return best_modifications[0]["details"]  # Choose the best modification
        return None

# ✅ Initialize AI Decision Engine
ai_decision_engine = AIDecisionEngine()
