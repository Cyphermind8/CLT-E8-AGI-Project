import json

class AIPerformanceLog:
    def __init__(self):
        self.log_file = "ai_performance_log.json"
        self.load_log()

    def load_log(self):
        try:
            with open(self.log_file, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            return {"modifications": []}

    def evaluate_performance(self):
        return len(self.load_log()["modifications"])

    def log_success(self, modification):
        log = self.load_log()
        log["modifications"].append({"modification": modification, "success": True})
        with open(self.log_file, "w") as file:
            json.dump(log, file, indent=4)
