import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

# ✅ Use 8-bit quantization to reduce RAM usage
quantization_config = BitsAndBytesConfig(load_in_8bit=True)

# ✅ Load CodeLLaMA-7B in optimized mode
model_name = "codellama/CodeLlama-7b-Python-hf"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, quantization_config=quantization_config, device_map="auto")

def analyze_code(code):
    """ Uses CodeLLaMA to analyze a given Python function and provide an optimized version. """
    input_prompt = f"""### Python Code Optimization Task ###

    **You are an AI software engineer specializing in high-performance Python programming.**
    
    - Below is a Python function that must be optimized.
    - **Your job is to return only the optimized function, nothing else.**
    - **Do NOT describe the function.**
    - **Do NOT repeat the original function.**
    - **Do NOT include docstrings, comments, or explanations.**
    - **Ensure the new function has significantly better efficiency (Big-O complexity).**

    ---
    **Function to Optimize:**
    ```python
    {code}
    ```

    **Optimized Version (Return ONLY valid Python code):**
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

    # ✅ Fix: Extract only the Python code
    if "```python" in result:
        result = result.split("```python")[-1].strip()  # Remove any text before the code
    if "```" in result:
        result = result.split("```")[0].strip()  # Remove any text after the code

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
