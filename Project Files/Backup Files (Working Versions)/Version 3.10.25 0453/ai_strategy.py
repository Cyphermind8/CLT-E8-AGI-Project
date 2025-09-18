from ai_memory import ai_memory
from ai_optimization import ai_optimization

class AIStrategy:
    def __init__(self):
        self.memory = ai_memory
        self.optimization = ai_optimization

    def define_learning_path(self):
        """AI determines which learning direction improves intelligence best."""
        best_mods = self.optimization.prioritize_best_modifications()
        if best_mods:
            return best_mods[0]["details"]  # Follow the highest-scoring improvement
        return "No strong learning path detected"

# ✅ Initialize AI Strategy System
ai_strategy = AIStrategy()
