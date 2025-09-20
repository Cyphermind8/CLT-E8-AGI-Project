import requests

# URL of the FastAPI endpoint where the file will be uploaded
url = 'http://localhost:8000/write_file'

# Path to the file you want to upload
file_path = 'C:/ai_project/ai_code_chunks/chunk_10.py'

# Open the file in read mode and read its content
with open(file_path, 'r') as file:
    content = file.read()

# Create the payload with the file content and the desired file path
data = {
    "filepath": "chunk_10.py",  # Provide the desired path for the file
    "content": content  # File content as a string
}

# Send the request to the API with the content in the correct format
response = requests.post(url, json=data)

# Check if the request was successful
if response.status_code == 200:
    print("File successfully uploaded.")
else:
    print(f"Failed to upload file. Status code: {response.status_code}")
    print(response.json())  # Print the detailed error message from the server
