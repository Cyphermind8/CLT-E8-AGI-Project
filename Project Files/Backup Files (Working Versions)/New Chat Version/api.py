from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import json
import subprocess
from ai_core import initialize_ai_core, ai_core

app = FastAPI()

initialize_ai_core()

class CodeAnalysisRequest(BaseModel):
    filename: str

class CodeModificationRequest(BaseModel):
    filename: str
    content: str

@app.get("/analyze_ai_code")
def analyze_ai_code(filename: str = "ai_core.py"):
    """Allows AI to analyze its own code."""
    if not os.path.exists(filename):
        raise HTTPException(status_code=404, detail="File not found.")
    
    with open(filename, "r", encoding="utf-8") as file:
        content = file.read()
    
    return {"filename": filename, "code_analysis": content[:1000]}  # Return first 1000 characters for review

@app.post("/modify_ai_code")
def modify_ai_code(request: CodeModificationRequest):
    """Allows AI to modify its own code."""
    if not os.path.exists(request.filename):
        raise HTTPException(status_code=404, detail="File not found.")
    
    with open(request.filename, "w", encoding="utf-8") as file:
        file.write(request.content)
    
    return {"message": "File successfully modified.", "filename": request.filename}

@app.post("/execute_file")
def execute_file(filepath: str):
    """Executes a specified Python file."""
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found.")
    
    try:
        result = subprocess.run(["python", filepath], capture_output=True, text=True)
        return {"output": result.stdout, "errors": result.stderr}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trigger_self_improvement")
def trigger_self_improvement():
    """Triggers AI self-improvement manually."""
    ai_core.trigger_self_improvement()
    return {"message": "AI successfully modified itself."}
