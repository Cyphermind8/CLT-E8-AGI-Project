# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Dict, List, Optional

import requests

DEFAULT_BASE = os.environ.get("OPENAI_BASE_URL", "http://127.0.0.1:1234/v1")
DEFAULT_MODEL = os.environ.get("MODEL", "openai/gpt-oss-20b")
DEFAULT_TEMP = float(os.environ.get("OPENAI_TEMPERATURE", "0"))
DEFAULT_MAX_TOKENS = int(os.environ.get("OPENAI_MAX_TOKENS", "600"))
DEFAULT_TIMEOUT = int(os.environ.get("OPENAI_REQUEST_TIMEOUT", os.environ.get("REQUESTS_TIMEOUT", "180")))

_JSON_FENCE = re.compile(r"^\s*```(?:json)?\s*$", re.IGNORECASE)
_CTRL_TAGS = re.compile(r"<\|[^|>]*\|>")  # strips tokens like <|channel|> / <|message|>

def _strip_fence_lines(s: str) -> str:
    lines = s.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    # strip leading fences
    while lines and _JSON_FENCE.match(lines[0]):
        lines = lines[1:]
    # strip trailing fences
    while lines and _JSON_FENCE.match(lines[-1]):
        lines = lines[:-1]
    return "\n".join(lines)

def _extract_json_object(text: str) -> Optional[str]:
    """
    Extract the first plausible JSON object from a noisy completion.
    Handles:
      - control tags like <|channel|>final ...
      - fenced blocks ```json ... ```
      - stray prose before/after
    """
    if not text:
        return None
    t = _CTRL_TAGS.sub("", text).strip()
    t = _strip_fence_lines(t).strip()

    # Fast path: already valid JSON
    try:
        json.loads(t)
        return t
    except Exception:
        pass

    # Heuristic: slice from first '{' to last '}' and try to load
    l = t.find("{")
    r = t.rfind("}")
    if l != -1 and r != -1 and r > l:
        candidate = t[l : r + 1]
        # Some models add trailing commas; quick sanitization (conservative)
        try:
            json.loads(candidate)
            return candidate
        except Exception:
            # Try trimming unmatched braces gradually from the right
            for rr in range(r, l, -1):
                try:
                    json.loads(t[l : rr + 1])
                    return t[l : rr + 1]
                except Exception:
                    continue
    return None

class LLMClient:
    def __init__(
        self,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout_s: Optional[int] = None,
    ):
        self.model = model or DEFAULT_MODEL
        self.base_url = (base_url or DEFAULT_BASE).rstrip("/")
        self.temperature = DEFAULT_TEMP if temperature is None else float(temperature)
        self.max_tokens = DEFAULT_MAX_TOKENS if max_tokens is None else int(max_tokens)
        self.timeout_s = DEFAULT_TIMEOUT if timeout_s is None else int(timeout_s)

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        resp = requests.post(url, json=payload, timeout=self.timeout_s)
        resp.raise_for_status()
        return resp.json()

    def chat_json(
        self,
        messages: List[Dict[str, str]],
        schema_hint: Optional[str] = None,
        max_tokens: Optional[int] = None,
        timeout_s: Optional[int] = None,
        retries: int = 1,
    ) -> Optional[Dict[str, Any]]:
        """
        Return parsed JSON dict or None. Robust to wrappers and minor noise.
        """
        mt = int(max_tokens or self.max_tokens)
        to = int(timeout_s or self.timeout_s)

        sys_gate = {"role": "system", "content": 'You must reply in strict JSON only. No prose.'}
        if messages and messages[0].get("role") != "system":
            messages = [sys_gate] + messages

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": mt,
            "stream": False,
        }

        exc: Optional[Exception] = None
        for _ in range(max(1, retries)):
            try:
                data = self._post("/chat/completions", payload)
                content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
                jtxt = _extract_json_object(content)
                if not jtxt:
                    continue
                obj = json.loads(jtxt)
                return obj
            except Exception as e:
                exc = e
                time.sleep(0.3)
        return None
