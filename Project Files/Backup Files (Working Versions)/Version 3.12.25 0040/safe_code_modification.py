import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

# ✅ Use 8-bit quantization to reduce RAM usage
quantization_config = BitsAndBytesConfig(load_in_8bit=True)

# ✅ Load CodeLLaMA-7B in optimized mode
model_name = "codellama/CodeLlama-7b-Python-hf"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, quantization_config=quantization_config, device_map="auto")

def analyze_code(code_snippet):
    """ Uses CodeLLaMA to analyze a given Python function and provide an optimized version. """
    input_prompt = f"""### Python Code Optimization Task ###

    **Step 1:** Read and understand the following function.
    **Step 2:** Identify inefficiencies and suggest improvements.
    **Step 3:** Rewrite the function in a more optimized way.

    **You MUST generate a new function. Do NOT repeat the original function.**

    ---
    **Function to Analyze:**
    ```python
    {code_snippet}
    ```

    **Step 1: Function Summary**  
    What does this function do?

    **Step 2: Efficiency Issues**  
    Explain why this function is inefficient.

    **Step 3: Optimized Version**  
    Generate a fully optimized function.

    **IMPORTANT: Return ONLY the new function, nothing else.**
    ```python
    """

    inputs = tokenizer(input_prompt, return_tensors="pt").to("cuda" if torch.cuda.is_available() else "cpu")

    # ✅ Fix: Use `max_new_tokens` instead of `max_length`
    outputs = model.generate(
        **inputs,
        max_new_tokens=512,  # Prevents input truncation while allowing AI to generate up to 512 tokens
        temperature=0.7,
        top_p=0.9,
        do_sample=True
    )

    result = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()

    return result

# ✅ Run a test when this script is executed
if __name__ == "__main__":
    print("\n🔄 Running Code Analysis Test...\n")

    # ✅ Sample Python function for AI analysis
    code_snippet = """ 
    def fibonacci(n):
        if n <= 0:
            return 0
        elif n == 1:
            return 1
        else:
            return fibonacci(n-1) + fibonacci(n-2)
    """

    # ✅ Run CodeLLaMA Analysis
    analysis_result = analyze_code(code_snippet)

    # ✅ Print Results
    print("\n📊 AI Code Analysis Report:\n")
    print(analysis_result)
