import json
from datetime import datetime
from ai_memory import ai_memory
from ai_benchmarking import calculate_benchmark_metrics

class AIRecursiveIntelligence:
    def __init__(self):
        self.memory = ai_memory

    def evaluate_past_modifications(self, n=10):
        """AI analyzes past modifications and determines intelligence progression."""
        modifications = self.memory.get_last_n_modifications(n=n)

        if not modifications:
            return "AI has insufficient data to evaluate past improvements."

        success_rate = sum(1 for mod in modifications if "AI Applied Modification" in mod["event"]) / len(modifications)
        entropy_scaling = sum(mod["entropy_score"] for mod in modifications) / len(modifications)

        intelligence_trend = "Improving" if entropy_scaling > 0.6 else "Needs Refinement"
        benchmark_results = calculate_benchmark_metrics()

        evaluation_result = {
            "success_rate": round(success_rate * 100, 2),
            "entropy_scaling": round(entropy_scaling, 2),
            "intelligence_trend": intelligence_trend,
            "benchmark_snapshot": benchmark_results
        }

        self.memory.log_modification("AI Intelligence Evaluation", evaluation_result, entropy_score=0.9)
        return evaluation_result

ai_recursive_intelligence = AIRecursiveIntelligence()
