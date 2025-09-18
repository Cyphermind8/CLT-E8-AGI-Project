import time
import requests
import datetime
import os
import json

def api_request_with_resilience(url, data, max_retries=5, base_delay=3):  # Increased base delay
    """
    Makes a request to the API with exponential backoff in case of failures.
    """
    log_file_path = "api_error_log.txt"
    cache_file_path = "ai_cache_v5.json"
    
    # Ensure log file exists
    if not os.path.exists(log_file_path):
        with open(log_file_path, "w") as log_file:
            log_file.write("--- API Error Log Started ---\n")
            log_file.flush()
    
    # Ensure cache file exists
    if not os.path.exists(cache_file_path):
        with open(cache_file_path, "w") as cache_file:
            json.dump({"last_api_call": 0, "github_repos": [], "arxiv_papers": [], "wikipedia_articles": []}, cache_file, indent=4)
            cache_file.flush()
    
    attempt = 0
    while attempt < max_retries:
        try:
            response = requests.post(url, json=data, timeout=20)  # Further increased timeout
            if response.status_code == 200:
                response_json = response.json()
                with open(cache_file_path, "r+") as cache_file:
                    cache = json.load(cache_file)
                    cache["last_api_call"] = time.time()
                    cache_file.seek(0)
                    json.dump(cache, cache_file, indent=4)
                    cache_file.truncate()
                return response_json
            else:
                error_message = f"⚠️ API Error: {response.status_code} at {datetime.datetime.now()} - Retrying in {base_delay ** attempt} sec..."
                print(error_message)
                with open(log_file_path, "a") as log_file:
                    log_file.write(error_message + "\n")
                    log_file.flush()
        except requests.exceptions.RequestException as e:
            error_message = f"❌ API Request Failed: {e} at {datetime.datetime.now()} - Retrying in {base_delay ** attempt} sec..."
            print(error_message)
            with open(log_file_path, "a") as log_file:
                log_file.write(error_message + "\n")
                log_file.flush()
        
        time.sleep(base_delay ** attempt)  # Longer exponential backoff
        attempt += 1
    
    final_message = "🚨 Maximum retries reached. API request failed."
    print(final_message)
    with open(log_file_path, "a") as log_file:
        log_file.write(final_message + "\n")
        log_file.flush()
    
    return None
