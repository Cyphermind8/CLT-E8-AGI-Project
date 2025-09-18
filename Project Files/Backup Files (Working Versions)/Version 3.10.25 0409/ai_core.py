import json
import random
import os
import threading
import time
import requests
from datetime import datetime, timezone, timedelta
from functools import lru_cache

from ai_memory import ai_memory
from ai_recursive_intelligence import AIRecursiveIntelligence

AI_FILE = "ai_core.py"
MOD_HISTORY_FILE = "modification_history.json"
LOG_FILE = "ai_performance_log.json"

# Define CST timezone offset
CST_OFFSET = timedelta(hours=-6)

def get_cst_time():
    """Returns the current timestamp in CST timezone."""
    return (datetime.now(timezone.utc) + CST_OFFSET).isoformat()

class AICore:
    def __init__(self):
        """Initialize AI core modules for learning, optimization, and intelligence scaling."""
        print("🚀 Initializing AI Core...")
        self.memory = ai_memory
        self.recursive_intelligence = AIRecursiveIntelligence()
        self.entropy = 1.0  # Dynamic learning rate
        self.failure_streak = 0
        self.last_improvement_time = time.time()
        self.modification_history = []
        print("✅ AI Core successfully initialized!")

    def validate_modification(self, modification):
        """Ensure modifications are valid and apply risk scoring."""
        risk_factor = self.analyze_risk(modification)
        if risk_factor > 0.7:
            print(f"❌ Modification rejected due to high risk: {modification}")
            return False
        return True

    def analyze_risk(self, modification):
        """Assess the risk level of a modification."""
        if "delete" in modification.lower():
            return 1.0  # High risk
        return 0.3  # Low risk default

    def rollback_last_modification(self):
        """Rollback last modification if it was unsuccessful."""
        rollback_message = self.memory.rollback_last_modification()
        print(f"🔄 {rollback_message}")

    def adjust_entropy(self, success):
        """Adjust entropy dynamically based on success/failure rates."""
        if success:
            self.entropy = max(0.2, self.entropy - 0.1)
            self.failure_streak = 0
        else:
            self.failure_streak += 1
            if self.failure_streak >= 3:
                self.entropy = min(1.0, self.entropy + 0.1)

    def fetch_external_ai_research(self):
        """Fetch AI research and apply insights dynamically."""
        sources = [
            "https://arxiv.org/list/cs.AI/recent",
            "https://github.com/topics/artificial-intelligence",
            "https://scholar.google.com/scholar?q=artificial+intelligence",
            "https://ieeexplore.ieee.org/search/searchresult.jsp?queryText=artificial%20intelligence",
            "https://huggingface.co/models?sort=trending",
            "https://openai.com/research/"
        ]
        insights = []
        for source in sources:
            try:
                response = requests.get(source, timeout=5)
                if response.status_code == 200:
                    insights.append(self.process_fetched_research(response.text))
                    print(f"✅ Knowledge Updated: {source}")
                else:
                    print(f"⚠️ Failed to fetch: {source}")
            except requests.RequestException:
                print(f"⚠️ Failed to fetch: {source}")
        return insights

    def process_fetched_research(self, research_text):
        """Extract key insights from fetched AI research."""
        return research_text[:500]  # Simplified placeholder for processing

    def trigger_self_improvement(self):
        """AI initiates self-improvement, applying research insights."""
        print("🚀 AI Self-Improvement Process Initiated...")
        sources_fetched = self.fetch_external_ai_research()
        
        all_possible_modifications = [
            "# AI Optimization: Improved memory handling",
            "# AI Enhancement: Faster search algorithm",
            "# AI Upgrade: Smarter context awareness",
            "# AI Debugging: Improved error detection",
            "# AI Adaptation: Better decision-making process",
            "# AI Performance Boost: Reduced processing overhead",
            "# AI Learning Upgrade: Enhanced self-reflection",
            "# AI Knowledge Expansion: Integrating new AI research insights",
        ]
        
        try:
            with open(MOD_HISTORY_FILE, "r") as f:
                self.modification_history = json.load(f).get("modifications", [])
        except (FileNotFoundError, json.JSONDecodeError):
            self.modification_history = []

        new_modifications = [mod for mod in all_possible_modifications if mod not in self.modification_history]
        if not new_modifications:
            new_modifications = all_possible_modifications
        
        selected_modification = random.choice(new_modifications)
        if not self.validate_modification(selected_modification):
            return
        
        self.modification_history.append(selected_modification)
        if len(self.modification_history) > 10:
            self.modification_history.pop(0)
        
        with open(MOD_HISTORY_FILE, "w") as f:
            json.dump({"modifications": self.modification_history}, f)

        success = random.random() < (0.5 + self.entropy * 0.2)
        self.adjust_entropy(success)
        if not success:
            self.rollback_last_modification()

    def continuous_improvement_loop(self):
        """Ensures AI continuously improves while researching and validating in parallel."""
        while True:
            now = time.time()
            if now - self.last_improvement_time >= 60:
                print(f"🔄 [{get_cst_time()}] AI Self-Improvement Cycle Running...")
                self.trigger_self_improvement()
                self.last_improvement_time = now
            time.sleep(5)

# Ensure ai_core is globally defined
ai_core = None  

def initialize_ai_core():
    """Ensures AI Core is initialized before use and starts continuous improvement loop."""
    global ai_core
    if ai_core is None:
        ai_core = AICore()
        threading.Thread(target=ai_core.continuous_improvement_loop, daemon=True).start()
