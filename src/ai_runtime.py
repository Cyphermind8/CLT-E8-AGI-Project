# FILE: src/ai_runtime.py
"""
ai_runtime.py — Single switch for LLM usage

Goals
- Default to OFFLINE (LLM disabled) so unit tests never depend on a live server.
- When enabled via env, use the OpenAI-compatible client (LM Studio, etc.).
- Keep a small, clean surface: llm_enabled(), chat().

Enable the LLM by setting:
  setx CLT_E8_LLM_ENABLED 1
  (then restart your shell, or set $env:CLT_E8_LLM_ENABLED="1" for the session)

Environment (.env):
  OPENAI_BASE_URL=http://127.0.0.1:1234/v1
  OPENAI_API_KEY=lm-studio
  MODEL=openai/gpt-oss-20b
"""

from __future__ import annotations
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

# Read model connection info
_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://127.0.0.1:1234/v1")
_API_KEY  = os.getenv("OPENAI_API_KEY", "lm-studio")
_MODEL    = os.getenv("MODEL", "openai/gpt-oss-20b")

def _truthy(s: Optional[str]) -> bool:
    return str(s or "").strip().lower() in {"1", "true", "yes", "on"}

# IMPORTANT: default disabled to keep tests offline & deterministic
_LLM_ENABLED = _truthy(os.getenv("CLT_E8_LLM_ENABLED", "0"))

_client = None

def llm_enabled() -> bool:
    """Return True if LLM calls are enabled by env (CLT_E8_LLM_ENABLED)."""
    return _LLM_ENABLED

def _get_client():
    """Lazily build the OpenAI-compatible client."""
    global _client
    if _client is None:
        from openai import OpenAI  # imported lazily to avoid dependency in pure-offline
        _client = OpenAI(base_url=_BASE_URL, api_key=_API_KEY)
    return _client

def chat(messages: List[Dict[str, Any]],
         *,
         temperature: float = 0.0,
         top_p: float = 0.95,
         max_tokens: int = 256) -> str:
    """
    Unified chat entry. If LLM is disabled, raise RuntimeError (callers should fall back).
    """
    if not llm_enabled():
        raise RuntimeError("LLM disabled by CLT_E8_LLM_ENABLED=0 (default).")

    client = _get_client()
    resp = client.chat.completions.create(
        model=_MODEL,
        messages=messages,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
    )
    return (resp.choices[0].message.content or "").strip()
