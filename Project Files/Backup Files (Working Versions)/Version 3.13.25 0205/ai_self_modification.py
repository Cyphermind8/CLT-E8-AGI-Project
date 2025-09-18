import json
import shutil
import time
import os
from code_analysis import analyze_code
from ai_performance_log import evaluate_performance

class AISelfModification:
    def __init__(self):
        self.file_to_modify = "ai_core.py"
        self.backup_folder = "backup/"
        os.makedirs(self.backup_folder, exist_ok=True)

    def backup_file(self):
        """Create a backup of the current AI core file before modification."""
        timestamp = int(time.time())
        backup_path = os.path.join(self.backup_folder, f"{self.file_to_modify}.bak-{timestamp}")
        shutil.copy(self.file_to_modify, backup_path)
        print(f"🛠️ Backup created: {backup_path}")

    def rollback(self):
        """Rollback to the last valid backup if modification fails."""
        backups = sorted([f for f in os.listdir(self.backup_folder) if f.startswith(self.file_to_modify)], reverse=True)
        if backups:
            last_backup = os.path.join(self.backup_folder, backups[0])
            shutil.copy(last_backup, self.file_to_modify)
            print(f"🔄 Rolled back to previous version: {last_backup}")
        else:
            print("⚠️ No backup available to restore!")

    def modify_code(self):
        """Modify AI core logic with validated improvements."""
        with open(self.file_to_modify, "r", encoding="utf-8") as f:
            original_code = f.read()

        print("🔹 AI analyzing code for improvements...")
        optimized_code = analyze_code(original_code)

        if not optimized_code.strip():
            print("❌ AI generated an empty modification. Aborting to prevent data loss.")
            return False

        with open(self.file_to_modify, "w", encoding="utf-8") as f:
            f.write(optimized_code)
        
        print(f"✅ AI successfully modified `{self.file_to_modify}`.")
        return True

    def test_functionality(self):
        """Test AI modifications before finalizing changes."""
        try:
            performance_gain = evaluate_performance()
            if performance_gain is None:
                print("⚠️ Performance evaluation returned no valid data. Rolling back.")
                return False
            print(f"🚀 AI performance gain: {performance_gain}x improvement.")
            return performance_gain > 1.0  # Ensure the change is positive
        except Exception as e:
            print(f"❌ AI modification caused an error: {e}")
            return False

    def start_self_modification(self):
        """Main loop for AI self-improvement."""
        print("\n🚀 AI Self-Modification Process Started...\n")
        self.backup_file()
        
        if not self.modify_code():
            print("❌ Modification was invalid. No changes applied.")
            return
        
        if not self.test_functionality():
            print("❌ AI detected issues in modified code. Rolling back...")
            self.rollback()
        else:
            print("✅ AI successfully modified the code with verified improvements.")

        print("\n🔄 AI self-improvement process completed.\n")

# Run AI Self-Modification Process
if __name__ == "__main__":
    ai_self_mod = AISelfModification()
    ai_self_mod.start_self_modification()
