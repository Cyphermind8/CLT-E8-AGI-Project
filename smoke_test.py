# C:\AI_Project\smoke_test.py
import os, sys
from dotenv import load_dotenv
import httpx
from openai import OpenAI

def die(msg: str, code: int = 1):
    print(f"❌ {msg}")
    sys.exit(code)

# 1) Load env
load_dotenv()
BASE_URL = os.getenv("OPENAI_BASE_URL")
API_KEY  = os.getenv("OPENAI_API_KEY") or "lm-studio"
MODEL    = os.getenv("MODEL")

print(f"🔎 OPENAI_BASE_URL = {repr(BASE_URL)}")
print(f"🔎 MODEL           = {repr(MODEL)}")

if not BASE_URL or not BASE_URL.startswith(("http://", "https://")):
    die("OPENAI_BASE_URL is missing or malformed. Expected something like 'http://127.0.0.1:1234/v1'.")

# 2) Probe /models to verify server is reachable
probe_url = BASE_URL.rstrip("/") + "/models"
try:
    resp = httpx.get(probe_url, timeout=5.0)
    print(f"🛰️  Probe GET {probe_url} -> {resp.status_code}")
    # Print a tiny snippet so we know it’s real JSON
    print("🛰️  Probe body (first 200 chars):", resp.text[:200])
    if resp.status_code != 200:
        die("Local server responded, but not with 200 OK. Check LM Studio Local Server settings.")
except Exception as e:
    die(f"Cannot reach local server at {probe_url}. Error: {e}")

# 3) Call the local model via OpenAI-compatible API
client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

try:
    completion = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": "Say hi in one short sentence."}],
        temperature=0.2,
    )
    content = completion.choices[0].message.content
    print("✅ Model reply:", content)
except Exception as e:
    die(f"OpenAI client call failed: {e}")
