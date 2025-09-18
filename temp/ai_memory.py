import json
import os

class AIMemory:
    def __init__(self, memory_file="modification_history.json"):
        """Initialize AI memory and load past modifications."""
        self.memory_file = memory_file
        self.load_memory()

    def load_memory(self):
        """Loads modification history from file."""
        if os.path.exists(self.memory_file):
            with open(self.memory_file, "r", encoding="utf-8") as f:
                try:
                    self.memory = json.load(f)
                except json.JSONDecodeError:
                    self.memory = {"modifications": []}
        else:
            self.memory = {"modifications": []}

    def save_memory(self):
        """Saves the modification history to file."""
        with open(self.memory_file, "w", encoding="utf-8") as f:
            json.dump(self.memory, f, indent=4)

    def log_modification(self, modification, success):
        """Logs a modification with success status."""
        entry = {
            "modification": modification,
            "success": success,
        }
        self.memory["modifications"].append(entry)
        self.save_memory()

    def validate_modification(self, modification):
        """Pre-execution validation logic for AI modifications."""
        risk_factor = self.analyze_risk(modification)
        if risk_factor > 0.7:  # Risk threshold
            return False, "⚠️ Modification rejected due to high risk."
        return True, "✅ Modification approved."

    def analyze_risk(self, modification):
        """Basic risk analysis function."""
        if "delete" in modification.lower():
            return 1.0  # High risk
        return 0.3  # Low risk for standard modifications

    def rollback_last_modification(self):
        """Reverts the last AI modification if it failed."""
        if "modifications" not in self.memory or not isinstance(self.memory["modifications"], list):
            return "🔹 No rollback needed (Invalid modification history format)."

        # Convert string-only history to dictionary format if necessary
        if all(isinstance(mod, str) for mod in self.memory["modifications"]):
            self.memory["modifications"] = [{"modification": mod, "success": False} for mod in self.memory["modifications"]]

        if self.memory["modifications"]:
            last_mod = self.memory["modifications"].pop()
            if isinstance(last_mod, dict) and not last_mod.get("success", False):
                rollback_entry = {
                    "modification": last_mod["modification"],
                    "success": False,
                    "rollback": True
                }
                self.memory["modifications"].append(rollback_entry)
                self.save_memory()
                return f"🔄 Rolled back modification: {last_mod['modification']}"
    
        return "🔹 No rollback needed."


# Ensure AI memory instance is available
ai_memory = AIMemory()
