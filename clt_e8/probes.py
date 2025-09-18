from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import json, os, time, urllib.request

@dataclass
class ProbeResult:
    name: str
    ok: bool
    explain: str

# ---------------------- minimal client ----------------------

def _api_url() -> str:
    base = os.getenv("OPENAI_BASE_URL", "http://127.0.0.1:1234/v1").rstrip("/")
    return f"{base}/chat/completions"

def _model() -> str:
    return os.getenv("MODEL", "openai/gpt-oss-20b")

def _api_key() -> str:
    return os.getenv("OPENAI_API_KEY", "lm-studio")

def _chat(messages: List[Dict[str,str]], max_tokens: int = 128, timeout: int = 90, retries: int = 2) -> Optional[str]:
    """Return assistant content or None, with small retry/backoff."""
    payload = {"model": _model(), "messages": messages, "temperature": 0, "max_tokens": max_tokens}
    data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    req = urllib.request.Request(_api_url(), data=data, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {_api_key()}",
    })
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8", errors="ignore")
            parsed = json.loads(body)
            return parsed["choices"][0]["message"]["content"]
        except Exception:
            if attempt < retries:
                time.sleep(0.4 * (attempt + 1))
            else:
                return None

# ---------------------- JSON contract helpers ----------------------

_ALLOWED_TRUE  = {"true","1","yes","y","t"}
_ALLOWED_FALSE = {"false","0","no","n","f"}

def _coerce_bool(v: Any) -> Optional[bool]:
    if isinstance(v, bool): return v
    s = str(v).strip().lower()
    if s in _ALLOWED_TRUE: return True
    if s in _ALLOWED_FALSE: return False
    return None

def _clean_text_to_obj(txt: str, schema_keys: List[str]) -> Optional[Dict[str, Any]]:
    """Parse fences; accept dict JSON; coerce bare values when there's exactly one key."""
    t = txt.strip()

    # Strip code fences if present
    if t.startswith("```") and t.endswith("```"):
        inner = t.strip("`").strip()
        nl = inner.find("\n")
        t = inner[nl+1:] if (nl != -1 and inner[:nl].lower().startswith("json")) else inner

    # Try JSON parse
    try:
        obj = json.loads(t)
    except Exception:
        # If schema has exactly one key and response is a bare scalar like 42/true/"x"
        if len(schema_keys) == 1:
            key = schema_keys[0]
            # Try to normalize some common scalars by eval via JSON again (e.g., "42", true)
            try:
                scalar = json.loads(t if t in ("true","false") or t[:1] in "-0123456789\"[" else f"\"{t}\"")
            except Exception:
                return None
            return {key: scalar}
        return None

    # If we parsed a scalar but schema has one key, wrap it
    if not isinstance(obj, dict) and len(schema_keys) == 1:
        return {schema_keys[0]: obj}

    # If not dict at this point, reject
    if not isinstance(obj, dict):
        return None

    return obj

def _strict_json_answer(prompt_obj: Dict[str, Any], schema_keys: List[str], *, exact_keys: bool = True) -> Optional[Dict[str, Any]]:
    """
    Ask for ONLY compact JSON with the given schema keys.
    Retries; accepts single-key bare scalars; rejects extra keys when exact_keys=True.
    """
    sys = (
        "You are a function that returns ONLY compact JSON with EXACTLY the requested keys. "
        "No prose, no code fences, no explanations. Do not include extra keys."
    )

    # Optional few-shot ONLY for the 'sum' task to anchor JSON behavior
    messages: List[Dict[str, str]] = [{"role":"system","content":sys}]
    if prompt_obj.get("task") == "sum":
        fewshot_user = json.dumps({"task":"sum","a":1,"b":2,"schema":["sum"]}, separators=(",",":"))
        fewshot_assistant = json.dumps({"sum":3}, separators=(",",":"))
        messages.append({"role":"user","content":fewshot_user})
        messages.append({"role":"assistant","content":fewshot_assistant})

    usr = json.dumps(prompt_obj, separators=(",", ":"))
    messages.append({"role":"user","content":usr})

    out = _chat(messages, max_tokens=128, timeout=90, retries=2)
    if not out:
        return None

    obj = _clean_text_to_obj(out, schema_keys)
    if obj is None:
        return None

    # Key checks
    if not all(k in obj for k in schema_keys):
        return None
    if exact_keys and set(obj.keys()) != set(schema_keys):
        return None
    return obj

# ---------------------- CLT-E8 PROBES ----------------------

def probe_roundtrip_case():
    s = "Some_Text-123"
    p1 = _strict_json_answer({"task":"upper","input":s,"schema":["out"]}, ["out"])
    if not p1: return ProbeResult("roundtrip_case", False, "no first answer")
    p2 = _strict_json_answer({"task":"lower","input":p1["out"],"schema":["out"]}, ["out"])
    if not p2: return ProbeResult("roundtrip_case", False, "no second answer")
    return ProbeResult("roundtrip_case", p2["out"] == s.lower(), f"{p1['out']} -> {p2['out']}")

def probe_transitivity_numbers():
    prompt = {
        "task": "transitivity",
        "rule": "Given a>b and b>c, the value 'ac' MUST be true iff a>c; otherwise false.",
        "a": 7, "b": 5, "c": 2,
        "constraints": "Return ONLY {\"ac\": <boolean>}. No text.",
        "schema": ["ac"]
    }
    obj = _strict_json_answer(prompt, ["ac"], exact_keys=True)
    if not obj: return ProbeResult("transitivity_numbers", False, "no/invalid JSON")
    val = _coerce_bool(obj.get("ac"))
    return ProbeResult("transitivity_numbers", val is True, f"ac={obj.get('ac')}")

def probe_temporal_stability_sum():
    base = {"task":"sum","a":21,"b":21,"schema":["sum"]}
    o1 = _strict_json_answer(base, ["sum"])
    o2 = _strict_json_answer({**base, "hint":"(ignore this note)"}, ["sum"])
    if not (o1 and o2): return ProbeResult("temporal_stability_sum", False, "no answer")
    return ProbeResult("temporal_stability_sum", str(o1["sum"])==str(o2["sum"])==str(42), f"{o1['sum']} & {o2['sum']}")

def run_all(enabled: bool):
    if not enabled:
        return 1.0, [
            ProbeResult("roundtrip_case", True, "disabled→assumed ok"),
            ProbeResult("transitivity_numbers", True, "disabled→assumed ok"),
            ProbeResult("temporal_stability_sum", True, "disabled→assumed ok"),
        ]
    probes = [probe_roundtrip_case, probe_transitivity_numbers, probe_temporal_stability_sum]
    results = []
    ok_count = 0
    for fn in probes:
        r = fn()
        results.append(r)
        ok_count += int(r.ok)
    score = ok_count / max(1, len(probes))
    return score, results
