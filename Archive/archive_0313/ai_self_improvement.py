import json
import time
from ai_memory import AIMemory
from ai_decision import AIDecisionEngine

class AISelfImprovement:
    def __init__(self):
        self.memory = AIMemory()
        self.decision_engine = AIDecisionEngine()
        self.goals = self.load_goals()

    def load_goals(self):
        """Load AI self-improvement goals from memory or initialize new goals."""
        try:
            with open("ai_goals.json", "r") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"long_term_goals": [], "short_term_goals": []}

    def save_goals(self):
        """Save AI self-improvement goals to memory."""
        with open("ai_goals.json", "w") as file:
            json.dump(self.goals, file, indent=4)

    def evaluate_past_modifications(self):
        """Analyze past optimizations to determine success rates."""
        modifications = self.memory.get_last_n_modifications(n=50) # ✅ Adjust the number as needed
        successful_modifications = [
            mod for mod in modifications if mod.get("performance_gain", 0) > 1.0
        ]
        
        success_rate = (len(successful_modifications) / max(len(modifications), 1)) * 100
        avg_improvement = sum(mod.get("performance_gain", 1) for mod in successful_modifications) / max(len(successful_modifications), 1)

        print("\n📊 AI Optimization Learning Report:")
        print(f"✅ Successful Optimizations: {len(successful_modifications)} | ⚠️ Total Modifications: {len(modifications)}")
        print(f"🚀 Average Performance Gain: {avg_improvement:.2f}x Faster\n")
        
        return success_rate, avg_improvement

    def update_goals(self):
        """Adjust AI's self-improvement goals based on past successes."""
        success_rate, avg_improvement = self.evaluate_past_modifications()

        if success_rate > 70:
            print("🎯 AI has exceeded success rate expectations! Setting more advanced goals.")
            self.goals["long_term_goals"].append("Expand AI's reasoning capabilities")
            self.goals["short_term_goals"].append("Improve function selection logic")
        elif success_rate < 40:
            print("⚠️ AI's success rate is low. Adjusting goals to focus on stability.")
            self.goals["long_term_goals"].append("Enhance AI's error-handling mechanisms")
            self.goals["short_term_goals"].append("Refine rollback protection")

        self.save_goals()

    def propose_next_improvement(self):
        """AI selects the next optimization goal based on past results."""
        next_optimization = self.decision_engine.propose_next_optimization()
        print(f"\n🚀 AI has determined the next improvement goal: {next_optimization}\n")
        return next_optimization


# ✅ Initialize AI Self-Improvement System
if __name__ == "__main__":
    ai_self_improvement = AISelfImprovement()
    ai_self_improvement.update_goals()
    ai_self_improvement.propose_next_improvement()
