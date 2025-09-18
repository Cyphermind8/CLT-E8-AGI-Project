from __future__ import annotations
from bench.json_sanitizer import parse_relaxed
# FILE: bench/run_bench.py
"""
CLT–E8 Bench (deterministic, file-based reports)

Goals:
- Preserve report schema for self_mod/gated_loop.py compatibility.
- Deterministic tool-call tasks with local execution (json_sort_values/json_merge).
- Canonicalize tool-call JSON (sorted keys) for true determinism.
- Robustness: retry once on empty/invalid outputs (handles local server hiccups).
- Reasonable token budgets to avoid truncation.

Outputs: reports/bench_<stamp>.json and .md
"""

import os, re, json, time, hashlib
from pathlib import Path
from typing import Any, Dict, List, Tuple, Callable
from dotenv import load_dotenv
from openai import OpenAI

# ---------- Paths & Env ----------
ROOT = Path(".").resolve()
REPORTS_DIR = ROOT / "reports"
REPORTS_DIR.mkdir(exist_ok=True)
load_dotenv()

BASE_URL = os.getenv("OPENAI_BASE_URL", "http://127.0.0.1:1234/v1")
API_KEY  = os.getenv("OPENAI_API_KEY", "lm-studio")
MODEL    = os.getenv("MODEL", "openai/gpt-oss-20b")
client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

# ---------- Local deterministic tools ----------
from src.tools.json_tools_v1 import execute_call

# ---------- Utils ----------
def det_hash(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:12]

def jdump(obj: Any, *, sort_keys: bool = False) -> str:
    """Compact JSON dump; optionally canonical (sorted keys)."""
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False, sort_keys=sort_keys)

def _chat(messages, *, temperature: float, max_tokens: int) -> str:
    r = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    content = r.choices[0].message.content
    return (content or "").strip()

def ask(prompt: str,
        sys: str = "Be exact. No extra words.",
        temperature: float = 0.0,
        max_tokens: int = 128,
        retries: int = 1) -> str:
    """
    Ask once; if empty output, retry once with a slightly stricter system note
    and a larger token budget. This defends against occasional local server hiccups.
    """
    out = _chat(
        [{"role":"system","content":sys},
         {"role":"user","content":prompt}],
        temperature=temperature, max_tokens=max_tokens
    )
    if out:
        return out

    if retries > 0:
        stricter = sys + " Answer exactly as specified. Do not output anything besides the requested answer."
        return ask(prompt, sys=stricter, temperature=0.0, max_tokens=max_tokens*2, retries=retries-1)
    return ""  # explicit empty

def ask_tool(prompt: str, retries: int = 1) -> Dict[str, Any]:
    """
    Ask for ONLY a compact JSON tool call. If parsing fails or schema missing,
    retry once with a stricter instruction and a higher token budget.
    """
    sys = (
        "Return ONLY one compact JSON object describing a tool invocation. "
        "No prose, no code fences. Keys: tool (string), args (object)."
    )
    out = ask(prompt, sys=sys, max_tokens=196, retries=0).strip()

    # Defensive cleanup for accidental fences
    if out.startswith("```"):
        out = out.strip("` \n")
        if out.lower().startswith("json"):
            out = out[4:].lstrip()

    try:
        call = parse_relaxed(out)
        if isinstance(call, dict) and "tool" in call and "args" in call:
            return call
        raise ValueError("Malformed tool call JSON")
    except Exception:
        if retries > 0:
            stricter = (
                "Return ONLY a single-line compact JSON object with keys exactly: "
                '"tool" and "args". No code fences, no commentary. Example: '
                '{"tool":"json_sort_values","args":{"obj":{"x":[3,1,2]},"key":"x"}}'
            )
            out2 = ask(prompt, sys=stricter, max_tokens=256, retries=0).strip()
            if out2.startswith("```"):
                out2 = out2.strip("` \n")
                if out2.lower().startswith("json"):
                    out2 = out2[4:].lstrip()
            call2 = parse_relaxed(out2)
            if not (isinstance(call2, dict) and "tool" in call2 and "args" in call2):
                raise ValueError("Malformed tool call JSON after retry")
            return call2
        raise

# ---------- Task set ----------
CheckFn = Callable[[str], bool]
Result = Dict[str, Any]

def run_once() -> List[Result]:
    tasks: List[Tuple[str, str, CheckFn, bool]] = [
        ("fib_20",
         "Return ONLY the 20th Fibonacci number as an integer (F(0)=0,F(1)=1).",
         lambda out: out.isdigit() and int(out)==6765,
         False),
        ("json_uppercase",
         'Given JSON {"a":1,"b":2}, return JSON with keys uppercased and no spaces.',
         lambda out: out == '{"A":1,"B":2}',
         False),
        ("regex_total",
         "From the text 'Order #A-9921 total=$43.50', extract ONLY the total dollar amount.",
         lambda out: re.fullmatch(r"\$?43\.50", out) is not None,
         False),
        ("mul_21_34",
         "In one short line: 21*34?",
         lambda out: out == "714",
         False),
        ("sum_big",
         "Sum ONLY these integers and print the result without commas: 12345 + 67890 - 1",
         lambda out: out.isdigit() and int(out)==80234,
         False),
        ("division",
         "Compute ONLY the integer result of 81/9.",
         lambda out: out == "9",
         False),

        # --- Tool-call tasks (deterministic) ---
        ("json_sort_values",
         "Use the JSON tool. Input obj={\"x\":[3,1,2]} and key=\"x\". "
         "Respond ONLY with compact JSON: {\"tool\":\"json_sort_values\",\"args\":{\"obj\":{\"x\":[3,1,2]},\"key\":\"x\"}}",
         # Check: parse model JSON, execute locally, compare canonical executed result
         lambda out: jdump(execute_call(parse_relaxed(out)), sort_keys=True) == '{"x":[1,2,3]}',
         True),

        ("extract_year",
         "From: 'Best album released in 1999, remastered later.' Return ONLY the 4-digit year.",
         lambda out: out == "1999",
         False),

        ("lowercase",
         "Lowercase this snake_case token and return ONLY the result: HELLO_WORLD",
         lambda out: out == "hello_world",
         False),

        ("reverse_digits",
         "Reverse the decimal digits of 1200 and return ONLY the result, zeroes preserved.",
         lambda out: out == "0021",
         False),

        ("json_merge",
         "Use the JSON tool. Merge a={\"a\":1} and b={\"b\":2} with policy prefer_b. "
         "Respond ONLY with: {\"tool\":\"json_merge\",\"args\":{\"a\":{\"a\":1},\"b\":{\"b\":2},\"policy\":\"prefer_b\"}}",
         lambda out: jdump(execute_call(parse_relaxed(out)), sort_keys=True) == '{"a":1,"b":2}',
         True),

        ("strict_bool",
         "Return ONLY the JSON-lowercase boolean literal for true.",
         lambda out: out == "true",
         False),
    ]

    results: List[Result] = []
    for name, prompt, check, is_tool in tasks:
        t0 = time.time()
        try:
            if is_tool:
                call_json = ask_tool(prompt, retries=1)
                # Canonicalized tool JSON for determinism
                out_text = jdump(call_json, sort_keys=True)
                executed = jdump(execute_call(call_json), sort_keys=True)
                ok = bool(check(out_text))
                latency = time.time() - t0
                results.append({
                    "name": name,
                    "ok": ok,
                    "output": out_text,
                    "executed": executed,
                    "latency_s": round(latency, 3),
                    "det_hash": det_hash(out_text),
                })
            else:
                out = ask(prompt, max_tokens=128, retries=1)
                ok = False
                try:
                    ok = bool(check(out))
                except Exception:
                    ok = False
                latency = time.time() - t0
                results.append({
                    "name": name,
                    "ok": ok,
                    "output": out[:400],
                    "latency_s": round(latency, 3),
                    "det_hash": det_hash(out),
                })
        except Exception as ex:
            latency = time.time() - t0
            results.append({
                "name": name,
                "ok": False,
                "output": f"[error] {ex}",
                "latency_s": round(latency, 3),
                "det_hash": det_hash(str(ex)),
            })
    return results

def run_eval(determinism_runs: int = 2) -> Dict[str, Any]:
    all_runs: List[List[Result]] = []
    for _ in range(determinism_runs):
        all_runs.append(run_once())

    # Determinism: require the same 'output' per task across runs
    determinism_ok = True
    aggregated: List[Result] = []
    for idx, first in enumerate(all_runs[0]):
        name = first["name"]
        outputs = [run[idx]["output"] for run in all_runs]
        ok_vals = [run[idx]["ok"] for run in all_runs]
        latencies = [run[idx]["latency_s"] for run in all_runs]
        same = all(o == outputs[0] for o in outputs)
        determinism_ok = determinism_ok and same
        aggregated.append({
            "name": name,
            "ok": all(ok_vals),
            "output": outputs[-1],
            "latency_s": round(sum(latencies)/len(latencies), 3),
            "det_hash": det_hash(outputs[-1]),
        })

    passed = sum(1 for r in aggregated if r["ok"])
    total = len(aggregated)
    success = {"passed": passed, "total": total, "rate": round(passed/total, 3)}
    avg_latency = {"avg_s": round(sum(r["latency_s"] for r in aggregated)/len(aggregated), 3)}
    summary = {
        "timestamp": time.strftime("%Y%m%d_%H%M%S"),
        "model": MODEL,
        "determinism_runs": determinism_runs,
        "success": success,
        "latency": avg_latency,
        "determinism_ok": bool(determinism_ok),
        "results": aggregated,
    }
    return summary

def write_report(summary: Dict[str, Any]) -> Dict[str, Any]:
    stamp = summary["timestamp"]
    out_json = REPORTS_DIR / f"bench_{stamp}.json"
    out_md   = REPORTS_DIR / f"bench_{stamp}.md"

    report = {"outputs": {"json": str(out_json), "md": str(out_md), "summary": summary}}
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        f"# Bench {stamp}",
        f"- Model: {summary['model']}",
        f"- determinism_runs: {summary['determinism_runs']}",
        f"- pass rate: {summary['success']['rate']} ({summary['success']['passed']}/{summary['success']['total']})",
        f"- avg latency: {summary['latency']['avg_s']} s",
        f"- determinism_ok: {summary['determinism_ok']}",
        "",
        "## Results",
    ]
    for r in summary["results"]:
        lines.append(f"- **{r['name']}**: {'PASS' if r['ok'] else 'FAIL'} | {r['latency_s']}s | det={r['det_hash']}")
    (REPORTS_DIR / f"bench_{stamp}.md").write_text("\n".join(lines), encoding="utf-8")
    return report

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--determinism", type=int, default=2)
    args = ap.parse_args()
    summary = run_eval(determinism_runs=args.determinism)
    report = write_report(summary)
    print(json.dumps(report, indent=2))
