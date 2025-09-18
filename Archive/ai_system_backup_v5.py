import aiohttp
import asyncio
import json
import os
import time
import threading
import shutil
import websockets
import psutil  # Ensure psutil is imported for system resource monitoring
from transformers import pipeline

# Define the generate_text function using Mistral LLM
generator = pipeline('text-generation', model='mistralai/Mistral-7B-Instruct-v0.1')

async def generate_text(prompt: str) -> str:
    """Generates text based on the provided prompt using Mistral."""
    try:
        # Generate text using the Mistral model
        result = generator(prompt, max_length=100, num_return_sequences=1)
        
        # Clean and handle any encoding issues
        generated_text = result[0]['generated_text']
        generated_text = generated_text.encode('utf-8', 'ignore').decode('utf-8')  # Ignore problematic characters
        
        return generated_text
    except Exception as e:
        print(f"❌ Error during text generation: {e}")
        return "Error generating text."

# Persistent memory storage file
MEMORY_FILE = "ai_memory_v5.json"
CODE_UPDATE_FILE = "ai_code_updates_v5.py"
AI_SOURCE_FILE = "ai_system_v5.py"
AI_BACKUP_FILE = "ai_system_backup_v5.py"
AI_LOG_FILE = "ai_performance_log_v5.json"
CACHE_FILE = "ai_cache_v5.json"
API_URL = "http://localhost:8000/generate"
LOG_SERVER_URL = "ws://localhost:8765"
cache = {}

# Import new modules
import knowledge_retrieval
import self_validation
import api_resilience

# Load persistent memory
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as file:
            return json.load(file)
    return {}

# Save persistent memory
def save_memory(data):
    with open(MEMORY_FILE, "w") as file:
        json.dump(data, file, indent=4)

# Load persistent cache
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as file:
            return json.load(file)
    return {}

# Save persistent cache
def save_cache(data):
    with open(CACHE_FILE, "w") as file:
        json.dump(data, file, indent=4)

cache = load_cache()

# Save performance logs

def log_performance(data):
    try:
        # Get system resource usage (CPU, memory)
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()

        # Add CPU and memory usage to the log data
        data["cpu_usage_percent"] = cpu_usage
        data["memory_usage_percent"] = memory.percent

        # Print data to verify it's being logged correctly
        print(f"CPU Usage: {cpu_usage}% | Memory Usage: {memory.percent}%")

        # Write performance data to the log files
        with open(AI_LOG_FILE, "a") as file:
            json.dump(data, file, indent=4)
            file.write("\n")
        
        # Log to the diagnostics file too (ai_diagnostics.log)
        with open("ai_diagnostics.log", "a") as file:
            file.write(f"CPU Usage: {cpu_usage}% | Memory Usage: {memory.percent}%\n")

    except Exception as e:
        print(f"❌ Critical Logging Failure: {e}")

# Direct AI Code Modification with Rollback and Validation
def apply_self_modification(change):
    try:
        shutil.copy(AI_SOURCE_FILE, AI_BACKUP_FILE)

        if not change.strip() or "Error:" in change:
            print("⚠️ Discarding invalid or empty modification.")
            return

        # Check if the change is already in the file
        with open(AI_SOURCE_FILE, "r") as file:
            existing_code = file.read()
            if change in existing_code:
                print("⚠️ Modification already applied. Skipping.")
                return

        with open(AI_SOURCE_FILE, "a") as file:
            file.write(f"\n# AI auto-improvement applied\n{change}\n")

        print("✅ AI successfully modified its own source code.")
        log_performance({"status": "Modification Applied", "change": change})
    except Exception as e:
        print(f"❌ AI self-modification failed: {e}. Reverting to last working version.")
        shutil.copy(AI_BACKUP_FILE, AI_SOURCE_FILE)
        log_performance({"status": "Rollback Performed", "error": str(e)})

async def auto_improve():
    print("🔄 AI is self-improving...")

    knowledge_data = knowledge_retrieval.retrieve_external_knowledge()
    applied_insights = knowledge_retrieval.apply_knowledge(knowledge_data)

    memory = load_memory()
    prompt = "Step 1: Identify a novel AI optimization. Do NOT repeat past improvements unless necessary. Prioritize impactful refinements."
    improvement = await generate_text(prompt)

    log_performance({"status": "Proposed Improvement", "improvement": improvement})

    if improvement.strip() in memory.get("past_improvements", []) or "Error:" in improvement:
        print("⚠️ Skipping invalid or duplicate improvement. Generating a new one...")
        log_performance({"status": "Improvement Skipped", "reason": "Duplicate or Error", "improvement": improvement})
        return

    if self_validation.validate_improvement(improvement):
        print(f"🚀 Applying Improvement: {improvement}")
        memory.setdefault("past_improvements", []).append(improvement.strip())
        memory["last_improvement"] = {"timestamp": time.ctime(), "change": improvement.strip()}
        save_memory(memory)
        log_performance(memory["last_improvement"])
        apply_self_modification(improvement)
    else:
        print("🔄 Retrying with a new approach...")
        log_performance({"status": "Improvement Rejected", "reason": "Validation Failed", "improvement": improvement})

    print("✅ AI improvement cycle completed.")

async def continuous_learning():
    interval = 120
    while True:
        try:
            await auto_improve()
            interval = max(45, min(interval * 0.9, 900))
            print(f"🔁 AI has completed a cycle. Next cycle in {interval:.0f} seconds.")
        except Exception as e:
            print(f"🚨 Error encountered: {str(e)}. Slowing down to prevent instability.")
            interval = min(1800, interval * 1.5)
        await asyncio.sleep(interval)

def start_ai():
    print("🚀 AI is now running in autonomous mode...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(continuous_learning())
    
if __name__ == "__main__":
    start_ai()

# AI auto-improvement applied
print("AI modification test")
