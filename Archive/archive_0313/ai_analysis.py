import os

class AIAnalysis:
    @staticmethod
    def analyze_code(filepath):
        if not os.path.exists(filepath):
            return f"Error: {filepath} not found"
        with open(filepath, "r") as f:
            return f.readlines()

ai_analysis = AIAnalysis()
print(ai_analysis.analyze_code("ai_core.py"))