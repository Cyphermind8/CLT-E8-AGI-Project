from ai_memory import ai_memory

class AIOptimization:
    def __init__(self):
        self.memory = ai_memory

    def prioritize_best_modifications(self):
        """Sort modifications by entropy score and return top improvements."""
        best_modifications = self.memory.get_highest_entropy_modifications(n=3)
        return best_modifications

    def discard_low_quality_modifications(self):
        """Remove modifications with low impact to keep AI evolving effectively."""
        self.memory.memory = [mod for mod in self.memory.memory if mod["entropy_score"] > 0.5]
        self.memory.save_memory()

# ✅ Initialize AI Optimization System
ai_optimization = AIOptimization()

