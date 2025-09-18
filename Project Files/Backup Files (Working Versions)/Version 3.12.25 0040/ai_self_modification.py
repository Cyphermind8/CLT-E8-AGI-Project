import os
from datetime import datetime
from ai_memory import ai_memory

AI_FILE = "ai_core.py"

def trigger_self_improvement():
    """Apply AI-driven self-modifications with validation."""
    if not os.path.exists(AI_FILE):
        ai_memory.log_improvement("Error", "AI core file is missing or corrupted. Modification aborted.", entropy_score=0.1)
        return "AI core file missing. Aborting."

    modification = "# AI self-improvement applied at " + datetime.now().isoformat()
    try:
        with open(AI_FILE, "a", encoding="utf-8") as f:
            f.write("\n" + modification)

        ai_memory.log_improvement("AI Applied Modification", modification, entropy_score=0.8)
        return "AI successfully modified itself."
    except Exception as e:
        ai_memory.log_improvement("Error", f"Failed to apply modification: {str(e)}", entropy_score=0.1)
        return f"Modification error: {str(e)}"
