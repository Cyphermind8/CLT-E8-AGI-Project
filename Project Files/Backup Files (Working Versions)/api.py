from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import json
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from ai_core import initialize_ai_core, ai_core

# Initialize FastAPI app
app = FastAPI()

# Ensure AI Core is initialized
initialize_ai_core()

# Path for modification history
MOD_HISTORY_FILE = "modification_history.json"

# Load Mistral-7B-Instruct
model_name = "mistralai/Mistral-7B-Instruct-v0.1"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name, 
    torch_dtype=torch.float16,  # Optimized for speed
    device_map="auto"
)

# ==========================
# 📌 CHAT API ENDPOINT
# ==========================
class ChatRequest(BaseModel):
    prompt: str

@app.post("/chat")
def chat_with_ai(request: ChatRequest):
    """Chat with AI using Mistral-7B-Instruct (Optimized)."""
    try:
        input_text = f"User: {request.prompt}\nAI:"
        inputs = tokenizer(input_text, return_tensors="pt").to("cuda")

        # Reduce max_length for faster responses
        output = model.generate(
            **inputs, 
            max_length=100,  
            do_sample=True, 
            temperature=0.7,  
            top_k=50,         
            top_p=0.9         
        )
        response = tokenizer.decode(output[0], skip_special_tokens=True)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

# ==========================
# 📌 NEW: FULL REPLACE API
# ==========================
class ReplaceCodeRequest(BaseModel):
    filename: str
    new_content: str

@app.post("/replace_code")
def replace_code(request: ReplaceCodeRequest):
    """Fully replaces a code file with new content."""
    try:
        if not os.path.exists(request.filename):
            raise HTTPException(status_code=404, detail="File not found.")
        
        with open(request.filename, "w", encoding="utf-8") as file:
            file.write(request.new_content)
        
        return {"message": f"{request.filename} successfully replaced."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================
# 📌 NEW: CREATE CODE FILE
# ==========================
class CreateCodeFileRequest(BaseModel):
    filename: str
    content: str

@app.post("/create_code_file")
def create_code_file(request: CreateCodeFileRequest):
    """Creates a new Python script."""
    try:
        if os.path.exists(request.filename):
            raise HTTPException(status_code=400, detail="File already exists.")
        
        with open(request.filename, "w", encoding="utf-8") as file:
            file.write(request.content)
        
        return {"message": f"New file {request.filename} successfully created."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================
# 📌 SELF-IMPROVEMENT ENDPOINT
# ==========================
@app.post("/trigger_self_improvement")
def trigger_self_improvement():
    """Manually triggers the AI self-improvement process."""
    try:
        ai_core.trigger_self_improvement()
        return {"message": "AI successfully modified itself."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================
# 📌 FILE MANAGEMENT ENDPOINTS
# ==========================
class FileData(BaseModel):
    filepath: str
    content: str

@app.get("/read_file")
def read_file(filepath: str):
    """Reads the content of a file."""
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            content = file.read()
        return {"filepath": filepath, "content": content}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found.")

@app.post("/write_file")
def write_file(data: FileData):
    """Writes content to a file."""
    try:
        with open(data.filepath, "w", encoding="utf-8") as file:
            file.write(data.content)
        return {"message": "File successfully written."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/modification_history")
def get_modification_history():
    """Retrieves the AI's modification history."""
    try:
        with open(MOD_HISTORY_FILE, "r") as file:
            history = json.load(file)
        return history
    except FileNotFoundError:
        return {"message": "No modification history found."}

# ==========================
# 📌 AI EXECUTION ENDPOINTS
# ==========================
@app.post("/execute_file")
def execute_file(filepath: str):
    """Executes a Python file and returns the output."""
    try:
        result = os.popen(f"python {filepath}").read()
        return {"filepath": filepath, "execution_result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/evaluate_ai_performance")
def evaluate_ai_performance():
    """Evaluates AI performance using pre-defined metrics."""
    try:
        ai_core.evaluate_performance()
        return {"message": "AI performance evaluation complete."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/log_modification")
def log_modification(data: dict):
    """Logs modifications made by AI."""
    try:
        with open(MOD_HISTORY_FILE, "a") as file:
            file.write(json.dumps(data) + "\n")
        return {"message": "Modification logged successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================
# 📌 SYSTEM STATUS ENDPOINT
# ==========================
@app.get("/system_status")
def system_status():
    """Returns the AI system status."""
    return {
        "status": "running",
        "ai_core_size": os.path.getsize("ai_core.py"),
        "modification_history_size": os.path.getsize(MOD_HISTORY_FILE) if os.path.exists(MOD_HISTORY_FILE) else "N/A"
    }
