import json
import time
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Load AI Model
model_name = "mistralai/Mistral-7B-Instruct-v0.1"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    device_map="auto",
    offload_folder="offload",  # Store offloaded layers to prevent OOM
    offload_state_dict=True,
    low_cpu_mem_usage=True  # Reduce memory overhead
)

# Memory Storage for AI Learning
MEMORY_FILE = "ai_memory.json"

class StructuredReasoningAI:
    def __init__(self):
        self.memory = self.load_memory()

    def load_memory(self):
        try:
            with open(MEMORY_FILE, "r") as f:
                data = json.load(f)
                # Ensure 'decisions' key exists
                if "decisions" not in data:
                    data["decisions"] = []
                return data
        except FileNotFoundError:
            return {"decisions": []}

    def save_memory(self):
        with open(MEMORY_FILE, "w") as f:
            json.dump(self.memory, f, indent=4)

    def analyze_code(self, code_snippet):
        """AI reviews a function and generates an optimized version."""
        input_prompt = f"""### AI Code Optimization Task ###

        **INSTRUCTION: Optimize the function while maintaining the correct logic.
        Avoid redundant calculations and improve efficiency.**

        **Function to Optimize:**
        ```python
        {code_snippet}
        ```

        **Return ONLY the optimized function below (no extra text):**
        """

        inputs = tokenizer(input_prompt, return_tensors="pt").to("cuda" if torch.cuda.is_available() else "cpu")
        outputs = model.generate(
            **inputs,
            max_new_tokens=512,
            temperature=0.7,
            top_p=0.9,
            do_sample=True
        )

        result = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
        return result

    def structured_decision(self, code_snippet):
        """AI applies structured reasoning before modifying code."""
        print("\n🔄 AI is analyzing the function and generating an optimized version...")

        # Check memory for past optimizations
        for entry in self.memory["decisions"]:
            if entry["code_review"] == code_snippet:
                print("\n🔍 AI found a past optimization. Using stored result.")
                return entry["optimized_code"]

        reasoning_output = self.analyze_code(code_snippet)

        print("\n🧠 AI-Generated Optimized Function:")
        print(reasoning_output)

        decision_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "code_review": code_snippet,
            "optimized_code": reasoning_output
        }

        self.memory["decisions"].append(decision_entry)
        self.save_memory()

        return reasoning_output

if __name__ == "__main__":
    print("\n✅ Running AI Structured Reasoning Test...\n")

    # Sample Python function for AI analysis
    code_snippet = """def fibonacci(n):
        if n <= 0:
            return 0
        elif n == 1:
            return 1
        else:
            return fibonacci(n-1) + fibonacci(n-2)
    """

    ai_reasoning = StructuredReasoningAI()
    optimized_code = ai_reasoning.structured_decision(code_snippet)

    print("\n🚀 AI Optimization Complete!\n")
