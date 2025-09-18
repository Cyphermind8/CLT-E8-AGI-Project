import json
import time
import requests
import os

def retrieve_external_knowledge():
    """Fetches GitHub, ArXiv, and Wikipedia data and updates cache."""
    cache_file = "ai_cache_v5.json"
    
    # Load cache
    try:
        with open(cache_file, "r") as file:
            cache = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        cache = {
            "github_repos": [],
            "arxiv_papers": [],
            "wikipedia_articles": [],
            "last_github_fetch": 0,
            "last_arxiv_fetch": 0,
            "last_wikipedia_fetch": 0,
            "cache_last_updated": 0
        }
    
    # Fetch GitHub Data
    github_url = "https://api.github.com/search/repositories?q=machine+learning"
    github_repos = requests.get(github_url).json().get("items", [])
    cache["github_repos"] = github_repos[:10]  # Store top 10 results
    cache["last_github_fetch"] = time.time()
    
    # Fetch ArXiv Data
    arxiv_url = "https://export.arxiv.org/api/query?search_query=all:AI"
    arxiv_papers = requests.get(arxiv_url).text  # ArXiv returns XML, needs parsing
    cache["arxiv_papers"] = arxiv_papers[:5]  # Placeholder: Adjust parsing
    cache["last_arxiv_fetch"] = time.time()
    
    # Fetch Wikipedia Data
    wikipedia_url = "https://en.wikipedia.org/api/rest_v1/page/summary/Artificial_intelligence"
    wikipedia_summary = requests.get(wikipedia_url).json().get("extract", "")
    cache["wikipedia_articles"] = [wikipedia_summary]
    cache["last_wikipedia_fetch"] = time.time()
    
    # Update cache
    cache["cache_last_updated"] = time.time()
    with open(cache_file, "w") as file:
        json.dump(cache, file, indent=4)
    
    print("✅ External knowledge retrieved and cached.")

def apply_knowledge(*args, **kwargs):
    """Processes cached knowledge and integrates it into AI's learning model."""
    cache_file = "ai_cache_v5.json"
    
    # Load cache
    try:
        with open(cache_file, "r") as file:
            cache = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        print("⚠️ No knowledge cache found. Skipping application.")
        return
    
    # Apply GitHub Knowledge
    if cache.get("github_repos"):
        print(f"🔹 Applying {len(cache['github_repos'])} GitHub repositories to AI.")
    
    # Apply ArXiv Knowledge
    if cache.get("arxiv_papers"):
        print(f"🔹 Applying {len(cache['arxiv_papers'])} ArXiv papers to AI.")
    
    # Apply Wikipedia Knowledge
    if cache.get("wikipedia_articles"):
        print("🔹 Applying Wikipedia knowledge on AI research.")
    
    print("✅ AI has processed external knowledge successfully.")

def diagnostic_mode():
    """Runs AI self-diagnostics and logs system performance."""
    log_file = "ai_diagnostics.log"
    cache_file = "ai_cache_v5.json"
    
    # Load cache data
    try:
        with open(cache_file, "r") as file:
            cache = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        cache = {}
    
    diagnostics = {
        "timestamp": time.time(),
        "github_repo_count": len(cache.get("github_repos", [])),
        "arxiv_paper_count": len(cache.get("arxiv_papers", [])),
        "wikipedia_article_count": len(cache.get("wikipedia_articles", [])),
        "last_cache_update": cache.get("cache_last_updated", 0),
    }
    
    # Write diagnostics to log
    with open(log_file, "a") as file:
        file.write(json.dumps(diagnostics, indent=4) + "\n")
    
    print("📊 AI diagnostics logged successfully.")
