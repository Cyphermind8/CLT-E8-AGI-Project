import requests
import os

# API endpoint
url = "http://localhost:8000/write_file"

# Directory containing the code chunks
directory = "C:/ai_project/ai_code_chunks/"

# Loop through all Python files and upload them one by one
for file_name in sorted(os.listdir(directory)):  # Sort to maintain order
    if file_name.endswith(".py"):  # Ensure only Python files are uploaded
        file_path = os.path.join(directory, file_name)

        # Read file content
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        # Prepare request payload
        data = {
            "filepath": file_name,  # Uploads with its own filename
            "content": content
        }

        # Send request to the API
        response = requests.post(url, json=data)

        # Print result
        if response.status_code == 200:
            print(f"✅ Successfully uploaded: {file_name}")
        else:
            print(f"❌ Failed to upload: {file_name} | Status: {response.status_code} | Error: {response.text}")
