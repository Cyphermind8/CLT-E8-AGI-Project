import os
import json
import subprocess
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

BASE_DIR = "C:/AI_Project"
LOG_FILE = os.path.join(BASE_DIR, "ai_improvement_logs.json")

class ImprovementRequest(BaseModel):
    filename: str
    modification: str

@app.get("/list_code_files")
def list_code_files():
    """List all Python files AI can modify."""
    try:
        files = [f for f in os.listdir(BASE_DIR) if f.endswith(".py")]
        return {"python_files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/read_code")
def read_code(filename: str):
    """Read the contents of a Python file."""
    filepath = os.path.join(BASE_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            content = file.read()
        return {"filename": filename, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/modify_code")
def modify_code(request: ImprovementRequest):
    """Modify and improve a Python script."""
    filepath = os.path.join(BASE_DIR, request.filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    try:
        # Read existing code
        with open(filepath, "r", encoding="utf-8") as file:
            original_content = file.read()
        
        # Apply modification
        improved_content = original_content + "\n" + request.modification
        
        # Save modified code
        with open(filepath, "w", encoding="utf-8") as file:
            file.write(improved_content)
        
        # Log improvement
        log_improvement(request.filename, request.modification)
        
        return {"message": "File modified successfully", "filename": request.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/execute_code")
def execute_code(filename: str):
    """Execute a modified Python script."""
    filepath = os.path.join(BASE_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    try:
        result = subprocess.run(["python", filepath], capture_output=True, text=True)
        return {"stdout": result.stdout, "stderr": result.stderr}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def log_improvement(filename, modification):
    """Log AI-generated code modifications."""
    log_entry = {"filename": filename, "modification": modification}
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
        else:
            logs = []
        logs.append(log_entry)
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=4)
    except Exception as e:
        print("Logging failed:", str(e))