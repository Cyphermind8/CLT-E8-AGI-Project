import requests
import os

# API endpoint
url = "http://localhost:8000/write_file"

# Directory containing the code chunks
directory = "C:/ai_project/ai_code_chunks/"

# Track files uploaded
files_uploaded = 0

print("\n🚀 Starting bulk upload...\n")

# Ensure all Python files are sorted and uploaded
file_list = sorted([f for f in os.listdir(directory) if f.endswith(".py")])

if not file_list:
    print("❌ No Python files found in the directory!")
else:
    print(f"🔍 Found {len(file_list)} files to upload.\n")

for file_name in file_list:
    file_path = os.path.join(directory, file_name)

    # Read file content
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    # Prepare request payload
    data = {
        "filepath": file_name,  # Uploads with its own filename
        "content": content
    }

    # Debugging: Print which file is being uploaded
    print(f"📤 Uploading: {file_name}...")

    # Send request to the API
    response = requests.post(url, json=data)

    # Print result
    if response.status_code == 200:
        print(f"✅ Successfully uploaded: {file_name}")
        files_uploaded += 1
    else:
        print(f"❌ Failed to upload: {file_name} | Status: {response.status_code} | Error: {response.text}")

# Final confirmation
print(f"\n🔥 Upload complete! {files_uploaded} files uploaded successfully.")
