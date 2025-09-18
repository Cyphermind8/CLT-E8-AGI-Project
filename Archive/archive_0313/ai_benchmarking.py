import os
import json
from datetime import datetime

# Define Paths
PROJECT_PATH = "C:/AI_Project/"
BENCHMARK_LOG = os.path.join(PROJECT_PATH, "ai_benchmark_results.json")
PERFORMANCE_LOG = os.path.join(PROJECT_PATH, "ai_performance_log.json")

# Moving average window for tracking long-term intelligence trends
MOVING_AVERAGE_WINDOW = 5

class AIBenchmarking:
    """Handles AI Benchmarking as an object instead of just functions."""
    
    def __init__(self):
        pass  # Initialize if needed

    def run_benchmark(self):
        """Runs AI benchmark calculations."""
        return calculate_benchmark_metrics()

def calculate_benchmark_metrics():
    """Calculates AI intelligence benchmark metrics based on performance logs."""
    data = load_performance_data()

    # ✅ Count valid AI modifications
    total_modifications = sum(1 for entry in data if "AI Applied Modification" in entry.get("event", ""))
    successful_modifications = sum(1 for entry in data if entry.get("success", False))

    # ✅ Detect rollbacks by checking if the last modification was undone
    rollbacks = sum(1 for i in range(len(data) - 1) if 
                    data[i]["event"] == "AI Applied Modification" and 
                    data[i + 1]["event"] == "AI Rolled Back Modification")

    # ✅ Enhanced intelligence scaling metric
    avg_entropy_scaling = sum(entry.get("entropy_score", 0.5) for entry in data) / len(data) if data else 0.5

    # ✅ Success & rollback rates
    success_rate = (successful_modifications / total_modifications) * 100 if total_modifications > 0 else 0
    rollback_rate = (rollbacks / total_modifications) * 100 if total_modifications > 0 else 0
    entropy_scaling = success_rate - rollback_rate

    benchmark_results = {
        "timestamp": datetime.now().isoformat(),
        "total_modifications": total_modifications,
        "successful_modifications": successful_modifications,
        "success_rate": round(success_rate, 2),
        "rollback_rate": round(rollback_rate, 2),
        "entropy_scaling": round(entropy_scaling, 2),
        "average_entropy_scaling": round(avg_entropy_scaling, 2),
        "success_rate_moving_avg": calculate_moving_average([success_rate]),
        "rollback_rate_moving_avg": calculate_moving_average([rollback_rate]),
        "entropy_scaling_moving_avg": calculate_moving_average([entropy_scaling])
    }

    return benchmark_results

def load_performance_data():
    """Loads AI performance logs to analyze modifications and learning trends."""
    if not os.path.exists(PERFORMANCE_LOG):
        return []
    try:
        with open(PERFORMANCE_LOG, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"🚨 Failed to load performance log: {str(e)}")
        return []

def calculate_moving_average(values, window=MOVING_AVERAGE_WINDOW):
    """Calculates a simple moving average for intelligence trend tracking."""
    if len(values) < window:
        return sum(values) / len(values) if values else 0
    return sum(values[-window:]) / window

def update_benchmark_log():
    """Logs AI benchmark metrics for daily analysis."""
    results = calculate_benchmark_metrics()

    try:
        # Ensure benchmark log exists before appending
        logs = []
        if os.path.exists(BENCHMARK_LOG):
            with open(BENCHMARK_LOG, "r", encoding="utf-8") as f:
                logs = json.load(f)

        logs.append(results)

        with open(BENCHMARK_LOG, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=4)

        print("✅ AI Benchmark updated successfully!")
    except Exception as e:
        print(f"🚨 Failed to update benchmark log: {str(e)}")

# Example usage
if __name__ == "__main__":
    update_benchmark_log()
