import json
import time

PERFORMANCE_LOG_FILE = "ai_performance_log.json"

class AIPerformanceLog:
    def __init__(self):
        self.log = self.load_log()

    def load_log(self):
        """Load past AI performance logs from file."""
        try:
            with open(PERFORMANCE_LOG_FILE, "r") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"modifications": []}

    def save_log(self):
        """Save AI performance log to file."""
        with open(PERFORMANCE_LOG_FILE, "w") as file:
            json.dump(self.log, file, indent=4)

    def log_performance(self, modification_name, performance_gain):
        """Log AI modification performance improvements."""
        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "modification": modification_name,
            "performance_gain": performance_gain
        }
        self.log["modifications"].append(entry)
        self.save_log()

    def evaluate_performance(self):
        """Evaluate AI's past modifications and calculate success rate and average improvement."""
        if not self.log["modifications"]:
            return 0, 0  # No past data

        success_count = sum(1 for mod in self.log["modifications"] if mod["performance_gain"] > 1)
        total_mods = len(self.log["modifications"])
        avg_improvement = sum(mod["performance_gain"] for mod in self.log["modifications"]) / total_mods

        return success_count, avg_improvement

# ✅ Initialize AI Performance Logger
ai_performance_log = AIPerformanceLog()

# ✅ Expose function for external imports
def evaluate_performance():
    return ai_performance_log.evaluate_performance()
