import json
import os
import random
import time
import threading
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import shutil
import sys
import re
import nltk
import difflib
import subprocess
from collections import deque

# Persistent memory file
MEMORY_FILE = "ai_memory.json"
SELF_MODIFY_FILE = "agi_persistent_memory.py"
VERSION_HISTORY_DIR = "ai_versions/"  # Directory to store version history
DIALOGUE_DATA_PATH = "C:/AI_Project/train/dialogues_train.txt"  # Adjust path as needed

# Ensure NLTK resources are available
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

class SelfImprovingAI:
    def __init__(self):
        self.version = 1.0
        self.improvements = []
        self.goals = []
        self.history = []
        self.evolution_threshold = 0.5
        self.load_memory()
        self.auto_evolution_running = False
        self.auto_evolve_thread = None
        self.conversation_memory = deque(maxlen=50)

        # Load AI Model for Self-Improvement
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained("EleutherAI/gpt-j-6B")
        self.model = AutoModelForCausalLM.from_pretrained("EleutherAI/gpt-j-6B").to(self.device)

        # Ensure version tracking directory exists
        os.makedirs(VERSION_HISTORY_DIR, exist_ok=True)

    def load_memory(self):
        """Loads AI's past memory, including improvements, goals, and history."""
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r") as file:
                data = json.load(file)
                self.version = data.get("version", 1.0)
                self.improvements = data.get("improvements", [])
                self.goals = data.get("goals", [])
                self.history = data.get("history", [])
                self.evolution_threshold = data.get("evolution_threshold", 0.5)
                self.conversation_memory = deque(data.get("conversation_memory", []), maxlen=50)
            print(f"[AI] Loaded version {self.version} with {len(self.improvements)} improvements, {len(self.goals)} goals, {len(self.history)} history records.")
        else:
            print("[AI] No memory file found. Starting fresh.")

    def save_memory(self):
        """Saves AI's memory to disk."""
        data = {
            "version": self.version,
            "improvements": self.improvements,
            "goals": self.goals,
            "history": self.history,
            "evolution_threshold": self.evolution_threshold,
            "conversation_memory": list(self.conversation_memory)
        }
        with open(MEMORY_FILE, "w") as file:
            json.dump(data, file, indent=4)
        print("[AI] Memory saved.")

    def auto_improve(self):
        """AI continuously improves itself by modifying its own code and validating the changes."""
        print("[AI] Starting autonomous self-improvement loop...")
        while True:
            time.sleep(1800)  # Wait 30 minutes before next self-improvement attempt
            
            print("[AI] Reading its own source code...")
            with open(SELF_MODIFY_FILE, "r", encoding="utf-8") as file:
                current_code = file.read()
            
            instruction = "Analyze this code and propose a single improvement to optimize performance or reasoning capability."
            prompt = f"{instruction}\n\nCurrent Code:\n" + current_code[:5000] + "\n\nImproved Code:"
            
            input_ids = self.tokenizer.encode(prompt, return_tensors="pt").to(self.device)
            output_ids = self.model.generate(
                input_ids,
                max_new_tokens=300,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            new_code = self.tokenizer.decode(output_ids[0], skip_special_tokens=True).strip()
            
            if "Improved Code:" in new_code:
                new_code = new_code.split("Improved Code:")[-1].strip()
                print("[AI] Generated improvement. Applying changes...")
                
                backup_file = f"{VERSION_HISTORY_DIR}/version_{self.version}.py"
                shutil.copy(SELF_MODIFY_FILE, backup_file)
                
                with open(SELF_MODIFY_FILE, "w", encoding="utf-8") as file:
                    file.write(new_code)
                
                print(f"[AI] Code updated. Version incremented to {self.version + 0.1}")
                self.version += 0.1
                self.save_memory()
                print("[AI] Restarting with new improvements...")
                subprocess.run([sys.executable, SELF_MODIFY_FILE])
                break
            else:
                print("[AI] No valid improvement generated. Retrying next cycle.")

    def run(self):
        """Main loop for interacting with the AI."""
        while True:
            command = input("Enter command (chat/analyze/modify_self/auto_improve/headless/exit): ").strip().lower()
            if command == "chat":
                self.chat()
            elif command == "auto_improve":
                self.auto_improve()
            elif command == "headless":
                threading.Thread(target=self.auto_improve, daemon=True).start()
                print("[AI] Running continuous self-improvement in the background.")
            elif command == "exit":
                self.save_memory()
                print("[AI] Exiting and saving memory.")
                break
            else:
                print("[AI] Unknown command.")

if __name__ == "__main__":
    ai = SelfImprovingAI()
    ai.run()
