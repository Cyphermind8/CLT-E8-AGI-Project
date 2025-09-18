import os
import shutil
from datetime import datetime

ROLLBACK_PATH = "C:/AI_Project/rollback/"

class AIRollback:
    def __init__(self, ai_file="C:/AI_Project/ai_core.py"):
        self.ai_file = ai_file
        self.ensure_rollback_directory()

    def ensure_rollback_directory(self):
        """Ensure rollback directory exists."""
        if not os.path.exists(ROLLBACK_PATH):
            os.makedirs(ROLLBACK_PATH)

    def create_backup(self):
        """Create a backup of AI core before modification."""
        backup_file = os.path.join(ROLLBACK_PATH, f"ai_core_backup_{datetime.now().isoformat()}.py")
        shutil.copy(self.ai_file, backup_file)
        print(f"✅ AI Backup Created: {backup_file}")

    def rollback_last_modification(self):
        """Restore last backup if AI modification fails."""
        backups = sorted(os.listdir(ROLLBACK_PATH), reverse=True)
        if backups:
            latest_backup = os.path.join(ROLLBACK_PATH, backups[0])
            shutil.copy(latest_backup, self.ai_file)
            print(f"🚨 AI Rolled Back to: {latest_backup}")

# ✅ Initialize AI Rollback System
ai_rollback = AIRollback()
