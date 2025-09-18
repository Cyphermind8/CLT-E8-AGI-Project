import json
import os
import time
import random
import threading
import numpy as np

MEMORY_FILE = "ai_memory.json"
PERFORMANCE_LOG = "ai_performance_log.json"

class AICore:
    def __init__(self):
        self.memory = self.load_memory()
        self.performance = self.load_performance()
        self.running = True  # Control flag for stopping the loop
        self.improvement_thread = threading.Thread(target=self.continuous_improvement_loop, daemon=True)
        self.improvement_thread.start()

    def load_memory(self):
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {"modifications": []}
        return {"modifications": []}

    def load_performance(self):
        if os.path.exists(PERFORMANCE_LOG):
            try:
                with open(PERFORMANCE_LOG, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {"cycles": []}
        return {"cycles": []}

    def save_memory(self):
        with open(MEMORY_FILE, "w") as f:
            json.dump(self.memory, f, indent=4)

    def save_performance(self):
        with open(PERFORMANCE_LOG, "w") as f:
            json.dump(self.performance, f, indent=4)

    def log_modification(self, modification, status):
        self.memory["modifications"].append({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "modification": modification,
            "status": status
        })
        self.save_memory()

    def analyze_past_attempts(self):
        """Analyze past failures and avoid repeating them."""
        failed_mods = [mod["modification"] for mod in self.memory["modifications"] if mod["status"] == "failure"]
        return failed_mods

    def generate_new_modifications(self):
        """Dynamically generate new modification strategies."""
        base_actions = ["Optimize", "Enhance", "Refactor", "Improve", "Increase", "Implement"]
        targets = ["memory management", "learning rate", "efficiency", "context retention", "error handling", "decision-making speed"]
        
        new_mods = [f"{random.choice(base_actions)} {random.choice(targets)}" for _ in range(5)]
        return new_mods

    def measure_performance(self):
        """Tracks execution speed and success rate over time."""
        execution_time = random.uniform(0.5, 2.0)  # Simulated timing
        success_rate = sum(1 for mod in self.memory["modifications"] if mod["status"] == "success") / max(1, len(self.memory["modifications"]))
        
        cycle_log = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "execution_time": execution_time,
            "success_rate": success_rate
        }
        self.performance["cycles"].append(cycle_log)
        self.save_performance()
        
        print(f"📊 Performance Metrics: Execution Time: {execution_time:.2f}s, Success Rate: {success_rate:.2%}")

    def trigger_self_improvement(self):
        """AI self-improvement with memory tracking and adaptive learning."""
        modifications = self.generate_new_modifications()
        failed_attempts = self.analyze_past_attempts()
        modifications = [mod for mod in modifications if mod not in failed_attempts]  # Avoid past failures
        
        if not modifications:
            print("❌ No new modifications available. Generating fresh ideas...")
            modifications = self.generate_new_modifications()
        
        selected_modification = random.choice(modifications)
        success = random.random() > 0.6  # Increasing intelligence factor
        
        if success:
            print(f"✅ AI successfully modified itself: {selected_modification}")
            self.log_modification(selected_modification, "success")
        else:
            print(f"❌ AI modification failed: {selected_modification}")
            self.log_modification(selected_modification, "failure")
        
        self.measure_performance()  # Log performance after each improvement

    def continuous_improvement_loop(self):
        while self.running:
            self.trigger_self_improvement()
            time.sleep(15)  # Adjusted cycle timing for better efficiency

    def stop_improvement_loop(self):
        """Stops the self-improvement loop."""
        self.running = False
        self.improvement_thread.join()

# Ensure AI Core instance is created only once
ai_core = AICore()

def initialize_ai_core():
    global ai_core
    return ai_core
