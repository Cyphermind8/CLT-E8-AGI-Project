# FILE: scripts/run_coherence_cycle.py
# UTF-8 (no BOM). Always hits LM Studio first, then runs the plan writer.

from __future__ import annotations
import os, sys, time
from pathlib import Path

# --- auto-root sys.path to project root ---
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def _probe_lmstudio() -> None:
    """
    List models then make a tiny chat call. Errors are logged, not raised.
    Ensures LM Studio shows activity every cycle.
    """
    os.environ.setdefault("OPENAI_BASE_URL", "http://127.0.0.1:1234/v1")
    os.environ.setdefault("OPENAI_API_KEY",  "lm-studio")
    os.environ.setdefault("MODEL",           "openai/gpt-oss-20b")
    try:
        from openai import OpenAI
    except Exception as e:
        log(f"LMStudio probe: openai package missing: {e!r}")
        return

    try:
        client = OpenAI(base_url=os.environ["OPENAI_BASE_URL"],
                        api_key=os.environ["OPENAI_API_KEY"])
        ids = [m.id for m in client.models.list().data]
        log(f"LMStudio /models OK ({len(ids)}) → {ids[:4]}{'...' if len(ids) > 4 else ''}")
    except Exception as e:
        log(f"LMStudio /models ERROR: {e!r}")
        return

    try:
        t0 = time.time()
        r = client.chat.completions.create(
            model=os.environ["MODEL"],
            messages=[{"role": "user", "content": "Reply with the single word: pong"}],
            temperature=0,
            max_tokens=5,
        )
        txt = (r.choices[0].message.content or "").strip()
        dt_ms = (time.time() - t0) * 1000
        log(f"LMStudio chat OK in {dt_ms:.1f} ms → {txt!r}")
    except Exception as e:
        log(f"LMStudio chat ERROR: {e!r}")

def main() -> int:
    log("cycle start")

    # 1) Always touch LM Studio so logs show activity
    _probe_lmstudio()

    # 2) Then do your planning pass (don’t crash the cycle if it fails)
    try:
        from src.ai.ai_learning import load_learning_state
        from src.ai.ai_decision import make_plan, write_plan
        state = load_learning_state()
        plan  = make_plan(state)
        out   = write_plan(plan)
        log(f"plan written → {out}")
    except Exception as e:
        log(f"pipeline skipped/errored: {e!r}")

    log("cycle end")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
