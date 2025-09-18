import json
from ai_memory import ai_memory

class AIProblemSolving:
    def __init__(self):
        self.memory = ai_memory

    def analyze_problems(self, problem_statement):
        """AI evaluates past modifications to determine if it can solve the problem."""
        solutions = []
        for entry in self.memory.memory:
            if problem_statement.lower() in entry["details"].lower():
                solutions.append(entry["details"])
        return solutions if solutions else ["No known solution found."]

    def generate_solution(self, problem_statement):
        """AI generates a new solution based on past learning."""
        past_solutions = self.analyze_problems(problem_statement)
        if "No known solution found." in past_solutions:
            return f"AI does not have prior knowledge to solve: {problem_statement}"
        return f"AI proposes a modification based on past success: {past_solutions[0]}"

# ✅ Initialize AI Problem-Solving System
ai_problem_solver = AIProblemSolving()
