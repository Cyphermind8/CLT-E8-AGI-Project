import json
import os

class AILearning:
    def __init__(self, memory_file="ai_memory.json"):
        self.memory_file = memory_file
        self.memory = self.load_memory()

    def load_memory(self):
        """Load AI memory from a JSON file or initialize a new structure."""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r", encoding="utf-8") as file:
                    return json.load(file)
            except json.JSONDecodeError:
                pass  # If file is corrupt, reset memory
        return {"modifications": []}

    def save_memory(self):
        """Save AI learning data back to the memory file."""
        with open(self.memory_file, "w", encoding="utf-8") as file:
            json.dump(self.memory, file, indent=4)

    def log_modification(self, file, original_code, improved_code, performance_gain):
        """Log successful AI optimizations for future learning."""
        modification_entry = {
            "file": file,
            "original_code": original_code,
            "improved_code": improved_code,
            "performance_gain": performance_gain
        }
        self.memory["modifications"].append(modification_entry)
        self.save_memory()
        print(f"✅ AI logged a new optimization for `{file}`.")

    def analyze_past_modifications(self):
        """Analyze past modifications to evaluate AI's self-improvement success."""
        modifications = self.memory.get("modifications", [])
        if not modifications:
            print("📊 No past modifications recorded yet.")
            return 0, 0  # No improvements to measure

        successful_mods = [mod for mod in modifications if mod["performance_gain"] > 0]
        success_rate = len(successful_mods) / len(modifications) * 100
        avg_improvement = sum(mod["performance_gain"] for mod in successful_mods) / max(len(successful_mods), 1)

        print(f"\n📊 AI Optimization Learning Report:")
        print(f"✅ Successful Optimizations: {len(successful_mods)} | ⚠️ Total Modifications: {len(modifications)}")
        print(f"🚀 Average Performance Gain: {avg_improvement:.2f}x Faster")

        return success_rate, avg_improvement

if __name__ == "__main__":
    ai_learning = AILearning()
    ai_learning.analyze_past_modifications()
