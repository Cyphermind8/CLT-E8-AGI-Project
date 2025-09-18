import os
from ai_memory import ai_memory

class AIValidation:
    def __init__(self, ai_file="C:/AI_Project/ai_core.py"):
        self.ai_file = ai_file

    def validate_modification(self, modification):
        """Ensure AI changes will not break core functionality."""
        if "delete" in modification or "remove" in modification:
            return False  # Prevent destructive changes
        if ai_memory.modification_exists(modification):
            return False  # Prevent redundant changes
        return True

# ✅ Initialize AI Validation System
ai_validation = AIValidation()
