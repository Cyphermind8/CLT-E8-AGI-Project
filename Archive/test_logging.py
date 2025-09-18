import json
import psutil

AI_LOG_FILE = "ai_performance_log_v5.json"

def log_performance(data):
    try:
        # Get system resource usage (CPU, memory)
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()

        # Add CPU and memory usage to the log data
        data["cpu_usage_percent"] = cpu_usage
        data["memory_usage_percent"] = memory.percent

        print(f"CPU Usage: {cpu_usage}% | Memory Usage: {memory.percent}%")

        # Write performance data to the log file
        with open(AI_LOG_FILE, "a") as file:
            json.dump(data, file, indent=4)
            file.write("\n")

    except Exception as e:
        print(f"❌ Critical Logging Failure: {e}")

# Manually trigger a log entry
log_performance({"status": "Manual Test Log"})
