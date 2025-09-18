from fastapi import FastAPI, HTTPException
import os
import json
from pydantic import BaseModel
from ai_core import initialize_ai_core

initialize_ai_core()  # Ensure AI Core is initialized before importing
from ai_core import ai_core
from ai_benchmarking import calculate_benchmark_metrics
from fastapi.responses import JSONResponse

app = FastAPI()

class ImprovementRequest(BaseModel):
    """Defines structure for AI self-improvement requests."""
    reason: str

@app.get("/")
def root():
    """Root endpoint to check API health."""
    return {"message": "AI Self-Improvement API is running!"}

@app.post("/trigger_self_improvement")
def trigger_self_improvement():
    """API endpoint to trigger AI self-improvement manually."""
    ai_core.trigger_self_improvement()  # Call method from the instance
    return {"message": "AI successfully modified itself."}

@app.post("/evaluate_ai_performance")
def evaluate_ai_performance():
    """API endpoint to evaluate AI performance using benchmarking."""
    performance_data = calculate_benchmark_metrics()
    return {"message": "AI performance evaluated.", "metrics": performance_data}

@app.post("/log_modification")
def log_modification(data: ImprovementRequest):
    """API endpoint to manually log a modification."""
    ai_core.memory.log_modification("Manual AI Modification", data.reason, entropy_score=0.9)
    return {"message": "Modification logged successfully!"}

@app.get("/get_modifications")
def get_modifications():
    """API endpoint to retrieve the last AI modifications."""
    modifications = ai_core.memory.get_last_n_modifications(n=10)
    return {"message": "Recent AI modifications retrieved.", "modifications": modifications}

@app.get("/{full_path:path}")
async def catch_all_requests(full_path: str):
    """Catch invalid requests and return a 404 JSON response."""
    return JSONResponse(status_code=404, content={"error": "Invalid API request"})
