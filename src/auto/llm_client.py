from __future__ import annotations
import json, os, urllib.request

DEFAULT_BASE = os.getenv("LM_STUDIO_BASE", "http://localhost:1234/v1")
DEFAULT_MODEL = os.getenv("LM_MODEL", "openai/gpt-oss-20b")

def chat(system: str, user: str, *, model: str | None = None, max_tokens: int = 768, temperature: float = 0.0) -> str:
    url = DEFAULT_BASE.rstrip("/") + "/chat/completions"
    payload = {
        "model": model or DEFAULT_MODEL,
        "messages": [{"role":"system","content":system},{"role":"user","content":user}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        data = json.loads(r.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]
