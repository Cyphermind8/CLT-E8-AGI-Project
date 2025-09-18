import json
from datetime import datetime

class AIMemory:
    def __init__(self, memory_file="ai_memory.json"):
        self.memory_file = memory_file
        self.memory = self.load_memory()

    def load_memory(self):
        """Load memory from file or create an empty structure if not found."""
        try:
            with open(self.memory_file, "r") as file:
                memory = json.load(file)

            # ✅ Ensure all modifications contain required fields
            for mod in memory.get("modifications", []):
                if "details" not in mod:
                    mod["details"] = "Unknown modification"
                if "entropy_score" not in mod:
                    mod["entropy_score"] = 0.0

            return memory

        except (FileNotFoundError, json.JSONDecodeError):
            return {"modifications": []}

    def save_memory(self):
        """Save current memory state to file."""
        with open(self.memory_file, "w") as file:
            json.dump(self.memory, file, indent=4)

    def log_modification(self, details, entropy_score):
        """Store a new modification with its entropy score."""
        self.memory["modifications"].append({
            "timestamp": datetime.now().isoformat(),
            "details": details,
            "entropy_score": entropy_score
        })
        self.save_memory()

    def get_last_n_modifications(self, n=10):
        """Retrieve the last N modifications from memory."""
        return self.memory["modifications"][-n:]

    def get_highest_entropy_modifications(self, n=5):
        """Retrieve the top N modifications sorted by entropy score."""
        return sorted(self.memory["modifications"], key=lambda x: x["entropy_score"], reverse=True)[:n]

# ✅ Initialize AI Memory
ai_memory = AIMemory()
