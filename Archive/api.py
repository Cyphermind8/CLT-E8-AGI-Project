from ai_system_v5 import AI_SOURCE_FILE
from ai_system_v5 import apply_self_modification
from fastapi import FastAPI, HTTPException
import json
import os
import time
import knowledge_retrieval  # Ensure module is imported
import psutil
from datetime import datetime

app = FastAPI()

import asyncio
from ai_system_v5 import continuous_learning

from fastapi import Request

@app.post("/modify_code")
async def modify_code(request: Request):
    """Allows external modification of AI source code."""
    data = await request.json()
    target_file = data.get("file", "")
    target_line = data.get("target_line", "")
    replacement = data.get("replacement", "")

    if not target_file or not target_line or not replacement:
        return {"error": "Invalid request. Must provide file, target_line, and replacement."}

    try:
        apply_self_modification(target_file, target_line, replacement)
        return {"status": "Modification applied successfully.", "file": target_file}
    except Exception as e:
        return {"error": f"Modification failed: {e}"}

@app.post("/trigger_improvement")
async def trigger_improvement():
    """Forces AI to analyze logs and apply an improvement."""
    try:
        await auto_improve()
        return {"status": "AI improvement cycle triggered."}
    except Exception as e:
        return {"error": f"Failed to trigger improvement: {e}"}

@app.on_event("startup")
async def start_continuous_learning():
    """Start AI continuous learning loop in the background when FastAPI starts."""
    asyncio.create_task(continuous_learning())  # ✅ Runs AI loop without blocking FastAPI

CACHE_FILE = "ai_cache_v5.json"
LOG_FILE = "ai_diagnostics.log"
AI_CODE_FILE = "ai_system_v5.py"

def get_cached_data(data_type):
    """Retrieve cached AI knowledge from the cache file."""
    try:
        with open(CACHE_FILE, "r") as file:
            cache = json.load(file)
        return cache.get(data_type, [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []

@app.get("/logs")
def get_logs():
    """Retrieve the latest AI diagnostics logs."""
    try:
        # Using the correct log file
        with open(LOG_FILE, "r") as file:  # LOG_FILE refers to ai_diagnostics.log
            logs = file.readlines()  # Read lines of the log file
        return {"logs": logs}
    except FileNotFoundError:
        # Provide more specific error message if the file is not found
        raise HTTPException(status_code=404, detail="Log file not found.")
    except Exception as e:
        # Catch any other errors that might occur and return them
        raise HTTPException(status_code=500, detail=f"Error reading logs: {e}")

@app.get("/cache")
def get_cache():
    """Retrieve AI cache data."""
    try:
        with open(CACHE_FILE, "r") as file:
            cache = json.load(file)
        return cache
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Cache file not found.")

from fastapi import FastAPI, Query
import shutil

app = FastAPI()

AI_SOURCE_FILE = "ai_system_v5.py"

import os

@app.post("/modify_ai")
async def modify_ai():
    """Directly modifies AI source code using a guaranteed PowerShell command."""
    try:
        modification = "# 🚀 AI System Direct Modification Test"
        file_path = "ai_system_v5.py"

        # 🚀 Use PowerShell Out-File to ensure writing
        os.system(f'powershell -Command "$modification=\'{modification}\'; Add-Content -Path {file_path} -Value $modification"')

        # 🚀 Force a save event
        os.system(f'powershell -Command "Add-Content -Path {file_path} -Value \'\'"')

        return {"status": "Success", "message": "AI modification applied via PowerShell."}
    
    except Exception as e:
        return {"detail": f"Error modifying AI: {e}"}

@app.post("/trigger_diagnostics")
def trigger_diagnostics():
    """Trigger AI self-diagnostics remotely, fetch knowledge, and log output."""
    
    # Check if retrieve_external_knowledge exists before calling it
    if hasattr(knowledge_retrieval, "retrieve_external_knowledge"):
        knowledge_retrieval.retrieve_external_knowledge()
    else:
        return {"status": "error", "message": "retrieve_external_knowledge() function is missing."}
    
    # Retrieve cached data
    diagnostics = {
        "timestamp": time.time(),
        "status": "AI diagnostics triggered",
        "github_repo_count": len(get_cached_data("github_repos")),
        "arxiv_paper_count": len(get_cached_data("arxiv_papers")),
        "wikipedia_article_count": len(get_cached_data("wikipedia_articles")),
    }
    
    # Write to log file
    try:
        with open(LOG_FILE, "a") as file:
            file.write(json.dumps(diagnostics, indent=4) + "\n")
    except Exception as e:
        return {"status": "error", "message": f"Failed to write to log: {e}"}
    
    return {"status": "success", "message": "Diagnostics triggered successfully."}

from ai_system_v5 import apply_self_modification

@app.post("/trigger_self_modify")
async def trigger_self_modify():
    """Trigger AI self-modification based on diagnostics."""
    try:
        apply_self_modification("ai_system_v5.py", "def some_function():", "# AI made this modification")
        return {"status": "success", "message": "AI self-modification triggered and applied."}
    except Exception as e:
        return {"error": f"Self-modification failed: {e}"}

@app.get("/get_performance_logs")
def get_performance_logs():
    """Retrieve the current performance and status of the AI system."""
    try:
        # Get system resource usage
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Retrieve the last modification timestamp
        last_mod_time = time.ctime(os.path.getmtime(AI_SOURCE_FILE))

        # Return the performance metrics
        performance_data = {
            "cpu_usage_percent": cpu_usage,
            "memory_usage_percent": memory.percent,
            "disk_usage_percent": disk.percent,
            "last_modification_time": last_mod_time
        }

        return performance_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving performance logs: {e}")

@app.get("/get_logs")
def get_logs():
    """Retrieve AI performance or diagnostic logs."""
    try:
        # Specify the log file you want to check (can be expanded to multiple logs)
        log_file = "ai_diagnostics.log"  # Change this if you're using a different log file

        if os.path.exists(log_file):
            with open(log_file, "r") as file:
                logs = file.readlines()  # Read the lines from the log file
            return {"logs": logs}
        else:
            raise HTTPException(status_code=404, detail="Log file not found.")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving logs: {e}")

@app.post("/trigger_self_improvement")
def trigger_self_improvement():
    """Analyze performance logs and trigger AI self-improvement."""
    try:
        # Get the performance logs
        performance_logs = get_logs()["logs"]

        # Example logic: Look for performance data (e.g., CPU usage)
        cpu_usage = None
        memory_usage = None

        # Loop through the logs and find the CPU and memory usage entries
        for log_entry in performance_logs:
            if "cpu_usage_percent" in log_entry.lower():
                cpu_usage = float(log_entry.split(":")[1].strip())  # Extract CPU usage
            if "memory_usage_percent" in log_entry.lower():
                memory_usage = float(log_entry.split(":")[1].strip())  # Extract Memory usage

        if cpu_usage is None or memory_usage is None:
            return {"status": "error", "message": "Could not find CPU or memory usage in logs."}

        if cpu_usage > 90 or memory_usage > 80:
            # Generate a code change to improve performance (just an example)
            new_code = """
            # Optimization: Improve CPU or memory performance by refactoring function XYZ
            def optimized_function():
                pass  # Optimized code goes here
            """
            # Apply the self-modification (improvement)
            from ai_system_v5 import apply_self_modification
            apply_self_modification(new_code)

            return {"status": "success", "message": "AI self-improvement triggered successfully."}
        else:
            return {"status": "no_action", "message": "No performance issues detected. No improvements made."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering self-improvement: {e}")
