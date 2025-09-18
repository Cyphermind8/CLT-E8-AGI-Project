import json
from ai_memory import ai_memory

class AILearning:
    def __init__(self):
        self.memory = ai_memory

    def analyze_past_modifications(self):
        """Review past modifications and determine success rates."""
        past_modifications = self.memory.get_last_n_modifications(n=10)
        
        if not past_modifications:
            print("\n📊 No past modifications recorded yet.\n")
            return

        success_count = 0
        total_improvement = 0

        for mod in past_modifications:
            entropy_score = mod.get("entropy_score", 0.0)
            details = mod.get("details", "Unknown modification")

            if entropy_score > 0.6:  # ✅ Threshold for "successful" optimizations
                success_count += 1
                total_improvement += entropy_score

            print(f"🔹 {details} | Entropy Score: {entropy_score}")

        if success_count > 0:
            avg_improvement = total_improvement / success_count
            print(f"\n📊 AI Optimization Learning Report:\n✅ Successful Optimizations: {success_count} | ⚠️ Regressions: {len(past_modifications) - success_count}\n🚀 Average Improvement: {avg_improvement:.2f}x Faster\n")
        else:
            print("\n⚠️ No significant improvements detected yet.\n")

    def log_successful_modification(self, details, entropy_score):
        """Log a successful optimization with meaningful details."""
        self.memory.log_modification(details, entropy_score)

# ✅ Initialize AI Learning
ai_learning = AILearning()

# ✅ Log a test optimization (example)
ai_learning.log_successful_modification("Optimized Fibonacci Sequence with Memoization", 1.25)

# ✅ Analyze learning progress
ai_learning.analyze_past_modifications()
