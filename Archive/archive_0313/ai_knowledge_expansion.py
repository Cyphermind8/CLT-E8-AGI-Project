import json
import os
from datetime import datetime

class AIKnowledgeExpansion:
    def __init__(self, memory_file="ai_memory.json"):
        self.memory_file = memory_file
        self.knowledge_base = self.load_memory()  # ✅ Fix: Ensures knowledge_base is a dict

    def load_memory(self):
        """Loads existing knowledge from memory."""
        if os.path.exists(self.memory_file):
            with open(self.memory_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}  # ✅ Fix: Ensure it's always a dict
        return {}

    def save_memory(self):
        """Saves updated knowledge to memory."""
        with open(self.memory_file, "w", encoding="utf-8") as f:
            json.dump(self.knowledge_base, f, indent=4)

    def ingest_data(self, topic, data):
        """Processes and stores structured knowledge."""
        if not isinstance(self.knowledge_base, dict):  # ✅ Extra safety check
            self.knowledge_base = {}

        if topic not in self.knowledge_base:
            self.knowledge_base[topic] = []

        self.knowledge_base[topic].append({
            "timestamp": datetime.now().isoformat(),
            "content": data
        })

        self.save_memory()
        print(f"✅ Knowledge Updated: {topic}")

    def retrieve_knowledge(self, topic):
        """Retrieves knowledge on a given topic."""
        return self.knowledge_base.get(topic, [])

# ✅ Example Usage
if __name__ == "__main__":
    ai_knowledge = AIKnowledgeExpansion()
    ai_knowledge.ingest_data("Quantum Computing", "Quantum entanglement can be used for secure communication.")
    print(ai_knowledge.retrieve_knowledge("Quantum Computing"))
