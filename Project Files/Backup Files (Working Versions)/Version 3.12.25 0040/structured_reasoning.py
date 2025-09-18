import torch
import time
from transformers import AutoModelForCausalLM, AutoTokenizer

# Load Model and Tokenizer
model_name = "mistralai/Mistral-7B-Instruct-v0.1"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    device_map="auto",
    torch_dtype=torch.float16
)

class StructuredReasoningAI:
    def __init__(self):
        self.memory = {"decisions": []}

    def analyze_code(self, code_snippet):
        """AI reviews a function and generates an optimized version."""
        input_prompt = f"""### AI Code Optimization Task ###

        **INSTRUCTION: Optimize the function while maintaining the correct Fibonacci sequence.
        Do NOT return a mathematical approximation. Return a function that correctly computes Fibonacci numbers using an efficient approach.
        Do NOT use recursion unless you implement memoization.**

        **Function to Optimize:**
        ```python
        {code_snippet}
        ```

        **Return ONLY the optimized function below (no extra text):**"""

        inputs = tokenizer(input_prompt, return_tensors="pt").to(model.device)
        outputs = model.generate(
            **inputs,
            max_new_tokens=1024,  # ✅ Ensures full function is generated
            temperature=0.7,
            top_p=0.9,
            do_sample=True
        )

        result = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
        return result

    def structured_decision(self, code_snippet):
        """AI applies structured reasoning before modifying code."""
        print("\n🔄 AI is analyzing the function and generating an optimized version...")

        reasoning_output = self.analyze_code(code_snippet)

        print("\n🧠 AI-Generated Optimized Function:")
        print(reasoning_output)

        decision_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "code_review": code_snippet,
            "optimized_code": reasoning_output
        }

        self.memory["decisions"].append(decision_entry)

        return reasoning_output

if __name__ == "__main__":
    print("\n✅ Running AI Structured Reasoning Test...\n")

    # Sample Python function for AI analysis
    code_snippet = """
    def fibonacci(n):
        if n <= 0:
            return 0
        elif n == 1:
            return 1
        else:
            return fibonacci(n-1) + fibonacci(n-2)
    """

    ai_reasoning = StructuredReasoningAI()
    optimized_code = ai_reasoning.structured_decision(code_snippet)
