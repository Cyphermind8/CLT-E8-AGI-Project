import json
from datetime import datetime
from ai_memory import ai_memory
from ai_predictive_reasoning import ai_predictive_reasoning

class AIGoalAdaptiveIntelligence:
    def __init__(self):
        self.memory = ai_memory
        self.predictive_engine = ai_predictive_reasoning
        self.current_goal = "Increase Intelligence Scaling"

    def set_new_goal(self, goal):
        """AI dynamically updates its primary learning objective."""
        self.current_goal = goal
        print(f"🚀 AI has updated its learning objective: {goal}")

    def assess_goal_progress(self):
        """AI evaluates how well it is progressing toward its defined goal."""
        modifications = self.memory.get_last_n_modifications(n=10)

        if not modifications:
            return "No modifications available for goal assessment."

        progress_score = sum(mod["entropy_score"] for mod in modifications) / len(modifications)

        return {
            "goal": self.current_goal,
            "progress_score": round(progress_score, 2),
            "status": "On Track" if progress_score > 0.7 else "Needs Adjustment"
        }

    def refine_learning_based_on_goal(self):
        """AI adapts its learning focus based on goal progress trends."""
        assessment = self.assess_goal_progress()
        if isinstance(assessment, str):  # No data available
            return "AI requires more modifications before refining its learning goal."

        if assessment["status"] == "Needs Adjustment":
            new_goal = "Optimize for Stability" if self.current_goal == "Increase Intelligence Scaling" else "Increase Intelligence Scaling"
            self.set_new_goal(new_goal)

# ✅ Initialize AI Goal-Adaptive Intelligence System
ai_goal_adaptive = AIGoalAdaptiveIntelligence()
