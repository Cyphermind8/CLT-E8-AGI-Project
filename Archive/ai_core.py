import aiohttp
import asyncio
import json
import os
import time
import threading
import shutil
import websockets
import torch
torch.cuda.empty_cache()
import psutil  # System monitoring
from transformers import pipeline
from torch.amp import autocast

from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline, BitsAndBytesConfig

# Enable 8-bit quantization to reduce memory usage
quantization_config = BitsAndBytesConfig(load_in_8bit=True)

# Load model efficiently with mixed precision
generator = pipeline(
    "text-generation",
    model="mistralai/Mistral-7B-Instruct-v0.1",
    device_map="auto",
    torch_dtype=torch.float16,  # Reduce memory usage
)

# Define text generation function
async def generate_text(prompt: str) -> str:
    """Generates text using Mistral-7B"""
    try:
        result = generator(prompt, max_length=50, num_return_sequences=1)
        return result[0]['generated_text']
    except Exception as e:
        print(f"❌ Error during text generation: {e}")
        return "Error generating text."

# Persistent memory storage
MEMORY_FILE = "ai_memory_v5.json"
AI_LOG_FILE = "ai_performance_log_v5.json"
CACHE_FILE = "ai_cache_v5.json"
AI_SOURCE_FILE = "ai_system_v5.py"

# Load/save functions
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as file:
            return json.load(file)
    return {}

def save_memory(data):
    with open(MEMORY_FILE, "w") as file:
        json.dump(data, file, indent=4)

def log_performance(data):
    """Logs system performance and AI events"""
    try:
        data["cpu_usage_percent"] = psutil.cpu_percent(interval=1)
        data["memory_usage_percent"] = psutil.virtual_memory().percent
        with open(AI_LOG_FILE, "a") as file:
            json.dump(data, file, indent=4)
            file.write("\n")
    except Exception as e:
        print(f"❌ Logging error: {e}")

import subprocess

def validate_python_file(target_file: str) -> bool:
    """Check if the Python file is still valid after modification."""
    try:
        result = subprocess.run(["python", "-m", "py_compile", target_file], capture_output=True, text=True)
        return result.returncode == 0  # Return True if no syntax errors
    except Exception as e:
        print(f"❌ Validation failed for `{target_file}`: {e}")
        return False

import os
import time

def force_save(file_path):
    """Forces a 'save' event so FastAPI detects the change."""
    time.sleep(1)  # Small delay for stability
    os.system(f'echo. >> "{file_path}"')  # Triggers a file change event in Windows

def apply_self_modification(target_file, target_line, replacement):
    """Modifies AI source code and forces a save event."""
    try:
        print(f"🚀 Attempting to modify {target_file}")

        with open(target_file, "r", encoding="utf-8") as file:
            lines = file.readlines()

        modification_applied = False
        with open(target_file, "w", encoding="utf-8") as file:
            for line in lines:
                if target_line in line:
                    file.write(replacement + "\n")
                    modification_applied = True
                    print(f"✅ Replaced: {target_line} → {replacement}")
                else:
                    file.write(line)

        if not modification_applied:
            with open(target_file, "a", encoding="utf-8") as file:
                file.write("\n" + replacement + "\n")
                print(f"✅ Appended modification: {replacement}")

        # 🚀 FORCE FASTAPI TO DETECT THE CHANGE
        force_save(target_file)

        print("🔄 Restarting FastAPI to apply changes...")
        os.system("uvicorn api:app --host 0.0.0.0 --port 8000 --reload")

    except Exception as e:
        print(f"❌ ERROR: {e}")

async def auto_improve():
    print("🔄 AI is self-improving...")

    # Suggest an improvement (text generation)
    improvement_task = asyncio.create_task(generate_text("Step 1: Identify an optimization."))
    improvement = await asyncio.wait_for(improvement_task, timeout=15)

    log_performance({"status": "Proposed Improvement", "improvement": improvement})

    # Prevent duplicates or invalid improvements
    if "Error" in improvement or improvement.strip() in load_memory().get("past_improvements", []):
        print("⚠️ Skipping duplicate or invalid improvement.")
        log_performance({"status": "Improvement Skipped", "reason": "Duplicate or Error"})
        return

    # 🔥 AI Self-Modification: Modify API settings & Logging
    if "adjust API timeout" in improvement.lower():
        apply_self_modification("api.py", "timeout=30", "timeout=20")  # Example modification
    if "increase logging detail" in improvement.lower():
        apply_self_modification("ai_system_v5.py", "logging_level = 'INFO'", "logging_level = 'DEBUG'")


    print(f"🚀 Applying Improvement: {improvement}")
    log_performance({"status": "Improvement Applied", "change": improvement})

    # 🔥 AI Self-Modification: Adjust Cycle Timing if Needed
    if "cycle timing" in improvement.lower():
        print("🚀 AI is modifying cycle timing!")
        apply_self_modification("interval = 60", "interval = 45")  # Example modification

    # Store past improvements
    memory = load_memory()
    memory.setdefault("past_improvements", []).append(improvement.strip())
    save_memory(memory)

async def continuous_learning():
    interval = 60  # Reduce cycle time for faster execution
    print("✅ AI Continuous Learning Loop Started.")
    log_performance({"status": "AI continuous learning started"})

    while True:
        try:
            print(f"🔄 AI cycle running. Next cycle in {interval} seconds.")
            log_performance({"status": "AI cycle running", "next_cycle": interval})

            # Run improvement function with timeout handling
            improvement_task = asyncio.create_task(auto_improve())

            try:
                await asyncio.wait_for(improvement_task, timeout=30)  # 🔥 Set a time limit for execution
            except asyncio.TimeoutError:
                print("⚠️ AI self-improvement cycle took too long. Skipping to next cycle.")
                log_performance({"status": "AI improvement timed out. Skipping to next cycle."})

            log_performance({"status": "Cycle completed", "next_cycle": interval})
            interval = max(30, min(interval * 0.9, 600))  # Adjust cycle timing

        except Exception as e:
            print(f"🚨 AI Error: {str(e)}. Slowing down.")
            log_performance({"status": "AI encountered an error", "error": str(e)})
            interval = min(1800, interval * 1.5)  # Slow down if errors happen

        await asyncio.sleep(interval)

def start_ai():
    """Start AI in autonomous mode"""
    print("🚀 AI is now running in continuous learning mode...")
    log_performance({"status": "AI started continuous learning"})
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(continuous_learning())
 
# ?? AI System Direct Modification Test

# ?? AI System Direct Modification Test

