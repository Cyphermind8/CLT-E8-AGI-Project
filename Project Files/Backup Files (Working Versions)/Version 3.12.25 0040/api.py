from fastapi import FastAPI
import threading
from ai_core import ai_core

app = FastAPI()

def start_continuous_improvement():
    """Starts the AI's continuous improvement loop in a separate thread."""
    improvement_thread = threading.Thread(target=ai_core.continuous_improvement_loop, daemon=True)
    improvement_thread.start()

@app.get("/system_status")
def system_status():
    """Returns the AI system status."""
    return {
        "status": "running",
        "current_goal": "Optimize decision-making efficiency",
        "memory_entries": len(ai_core.mod_history)
    }

@app.post("/trigger_self_improvement")
def trigger_self_improvement():
    """Manually triggers an AI self-improvement cycle."""
    try:
        ai_core.apply_modification()  # ✅ FIX: Correct function name
        return {"message": "AI successfully modified itself."}
    except Exception as e:
        return {"error": f"Error triggering self-improvement: {str(e)}"}

# 🔥 Start Continuous Improvement When API Boots
start_continuous_improvement()
