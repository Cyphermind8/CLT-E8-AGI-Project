from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Corrected local model path
model_path = "C:/ai_project/models/mistral"


# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=False)

# Load model
model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16, device_map="auto")

# Test inference
prompt = "What is the meaning of life?"
inputs = tokenizer(prompt, return_tensors="pt").to("cuda")

# Generate output
with torch.no_grad():
    output = model.generate(**inputs, max_length=100)

# Decode and print response
response = tokenizer.decode(output[0], skip_special_tokens=True)
print("AI Response:", response)
