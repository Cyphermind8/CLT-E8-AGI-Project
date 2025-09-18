import json
import time
from ai_memory import ai_memory

class AIDecisionEngine:
    def __init__(self):
        self.memory = ai_memory

    def evaluate_modification_success(self, modification):
        """Check if a past modification improved AI intelligence."""
        past_modifications = self.memory.get_last_n_modifications(n=10)
        for past_mod in past_modifications:
            if "details" in past_mod and modification in past_mod["details"]:
                return past_mod.get("entropy_score", 0) > 0.6  # Only keep high-impact changes
        return False

    def score_optimizations(self):
        """Assigns scores to past optimizations and picks the best ones."""
        past_modifications = self.memory.get_last_n_modifications(n=20)
        scored_modifications = []

        for mod in past_modifications:
            if "details" in mod:
                score = mod.get("performance_gain", 1) * mod.get("entropy_score", 1)
                scored_modifications.append({"details": mod["details"], "score": score})

        return sorted(scored_modifications, key=lambda x: x["score"], reverse=True)

    def select_best_modification(self):
        """Choose the highest-ranked improvement from memory."""
        best_modifications = self.score_optimizations()
        if best_modifications:
            return best_modifications[0]["details"]  # Choose the best modification
        return None

    def propose_next_optimization(self):
        """AI decides the next function to optimize."""
        best_modification = self.select_best_modification()
        if best_modification:
            print(f"🚀 AI has selected the next optimization: {best_modification}")
            return best_modification
        else:
            print("⚠️ AI could not determine the next optimization based on past results.")
            return None

# ✅ Initialize AI Decision Engine
ai_decision_engine = AIDecisionEngine()

# Run AI decision-making process
if __name__ == "__main__":
    next_optimization = ai_decision_engine.propose_next_optimization()
