import torch
import time
from transformers import AutoModelForCausalLM, AutoTokenizer

# Load model and tokenizer
model_name = "mistralai/Mistral-7B-Instruct-v0.1"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    device_map="auto"
)

class StructuredReasoningAI:
    def __init__(self):
        """Initialize AI memory for structured reasoning."""
        self.memory = {"decisions": []}

    def analyze_code(self, code_snippet):
        """AI reviews a function and generates an optimized version."""
        input_prompt = f"""### AI Code Optimization Task ###
        
        **INSTRUCTION: Return ONLY the optimized function. Do NOT include explanations.**

        **Function to Optimize:**
        ```python
        {code_snippet}
        ```

        **Return ONLY the optimized function below (no extra text):**"""

        inputs = tokenizer(input_prompt, return_tensors="pt").to("cuda" if torch.cuda.is_available() else "cpu")

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
    ai_reasoning.structured_decision(code_snippet)
