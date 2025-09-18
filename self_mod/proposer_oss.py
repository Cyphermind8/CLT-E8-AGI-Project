# FILE: self_mod/proposer_oss.py
"""
GPT-OSS proposer for minimal, safe code modifications.

- Reads a target file, asks the local model for a tiny improvement.
- Returns N candidate full-file replacements with short rationales.
- No changes are applied here; see gated_loop.py for testing/acceptance.

Assumptions:
- OPENAI_BASE_URL / OPENAI_API_KEY / MODEL are set in .env for LM Studio.
- This module doesn't require internet; it talks to the local server.
"""
from __future__ import annotations
import os, json, random
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()
try:
    from openai import OpenAI
except Exception as e:
    raise SystemExit("Missing dependency 'openai'. Install with: pip install openai python-dotenv") from e

BASE_URL = os.getenv('OPENAI_BASE_URL', 'http://127.0.0.1:1234/v1')
API_KEY  = os.getenv('OPENAI_API_KEY', 'lm-studio')
MODEL    = os.getenv('MODEL', 'openai/gpt-oss-20b')

def _client() -> OpenAI:
    return OpenAI(base_url=BASE_URL, api_key=API_KEY)

SYSTEM_PROMPT = """\
You are a cautious code optimizer. Rule of engagement:
- Prefer micro-diffs: small, local improvements only.
- Preserve public APIs and behavior. Do not rename externally used functions.
- Keep style consistent; add docstrings where useful.
- Never add network/system calls or file writes.
- Output JSON only: {"description": str, "content": str} where content is the FULL revised file.
"""

def propose_candidates(target_path: str, n: int = 3, diversity: float = 0.1) -> List[Dict[str,str]]:
    p = Path(target_path)
    if not p.exists():
        raise FileNotFoundError(f"Target not found: {p}")
    original = p.read_text(encoding='utf-8')
    client = _client()
    out = []
    for i in range(max(1, n)):
        temp = max(0.0, min(1.0, diversity * (i+1) / n))  # small temperature ramp
        messages = [
            {"role":"system","content": SYSTEM_PROMPT},
            {"role":"user","content": f"File path: {p.name}\n---BEGIN FILE---\n{original}\n---END FILE---\n\nTask: Propose a minimal improvement that could reduce latency or cognitive steps or improve clarity without changing behavior. Return JSON with 'description' and 'content' (full file)."}
        ]
        r = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=temp,
            max_tokens=2048
        )
        text = r.choices[0].message.content.strip()
        try:
            obj = json.loads(text)
            desc = str(obj.get('description','')).strip()
            content = str(obj.get('content','')).rstrip() + "\n"
            if content and len(content) > 10:
                out.append({"description": desc, "content": content})
        except Exception:
            # If JSON parse fails, skip candidate
            continue
    return out
