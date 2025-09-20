import os
import json
from datetime import datetime, timedelta

# Define Paths
PROJECT_PATH = "C:/AI_Project/"
LOOP_DETECTION_LOG = os.path.join(PROJECT_PATH, "loop_detection_log.json")
PERFORMANCE_LOG = os.path.join(PROJECT_PATH, "ai_performance_log.json")

# Configuration
LOOP_THRESHOLD = 3  # Number of repeated modifications before flagging a loop
CRITICAL_LOOP_THRESHOLD = 6  # AI will pause modifications if this threshold is reached
TIME_WINDOW = timedelta(minutes=10)  # Time frame to check repeated modifications

def load_performance_data():
    """Loads AI performance logs to analyze modification patterns."""
    if not os.path.exists(PERFORMANCE_LOG):
        return []
    try:
        with open(PERFORMANCE_LOG, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"🚨 Failed to load performance log: {str(e)}")
        return []

def detect_looping_behavior():
    """Detects if AI is stuck in a modification loop based on frequency and time-based repetition."""
    data = load_performance_data()
    modification_history = {}
    loop_detected = False
    critical_loop_detected = False
    now = datetime.now()

    for entry in data:
        mod = entry.get("modification", "")
        timestamp = datetime.fromisoformat(entry.get("timestamp", now.isoformat()))
        
        # Only consider modifications within the defined TIME_WINDOW
        if now - timestamp > TIME_WINDOW:
            continue

        if mod in modification_history:
            modification_history[mod]["count"] += 1
            modification_history[mod]["last_seen"] = timestamp
        else:
            modification_history[mod] = {"count": 1, "last_seen": timestamp}

    # Detect modification loops
    looping_modifications = {mod: details["count"] for mod, details in modification_history.items() if details["count"] >= LOOP_THRESHOLD}
    critical_loops = {mod: details["count"] for mod, details in modification_history.items() if details["count"] >= CRITICAL_LOOP_THRESHOLD}

    if looping_modifications:
        loop_detected = True
    if critical_loops:
        critical_loop_detected = True

    return looping_modifications, loop_detected, critical_loops, critical_loop_detected

def log_loop_detection(loop_data, critical_loops):
    """Logs detected modification loops for debugging and stability analysis."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "loop_detected": bool(loop_data),
        "looping_modifications": loop_data,
        "critical_loop_detected": bool(critical_loops),
        "critical_loops": critical_loops
    }

    try:
        logs = []
        if os.path.exists(LOOP_DETECTION_LOG):
            with open(LOOP_DETECTION_LOG, "r", encoding="utf-8") as f:
                logs = json.load(f)

        logs.append(log_entry)

        with open(LOOP_DETECTION_LOG, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=4)

        if critical_loops:
            print(f"🚨 CRITICAL LOOP DETECTED! AI is modifying the same code too frequently: {critical_loops}. AI self-modification will be paused.")
            return False  # AI should stop modifications if critical loops are detected
        elif loop_data:
            print(f"⚠️ Loop Warning: AI is modifying the same code repeatedly: {loop_data}")
        else:
            print("✅ No modification loops detected. AI is evolving normally.")

    except Exception as e:
        print(f"🚨 Failed to update loop detection log: {str(e)}")

# Example usage
if __name__ == "__main__":
    detected_loops, loop_detected, critical_loops, critical_loop_detected = detect_looping_behavior()
    should_continue = log_loop_detection(detected_loops, critical_loops)
    if should_continue is False:
        print("⏸ AI Self-Modification Paused Due to Critical Loop Detection.")
