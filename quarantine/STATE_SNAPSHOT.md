# AI_Project Snapshot (2025-09-15 23:05)

**Goal:** hands-off CI with strict gates; continuous self-improvement; zero human intervention.

**Infra:**
- Windows PowerShell 5 host
- LM Studio server: http://127.0.0.1:1234/v1
- MODEL=openai/gpt-oss-20b, OPENAI_TEMPERATURE=0, OPENAI_MAX_TOKENS=600
- Key entrypoints: scripts\run_ci.ps1, self_mod\gated_loop.py

**Recent highlights:**
- Bench: 12/12 passing, determinism_ok=true (avg latency ~3.5–6.0s depending on run)
- Micro workspace: avg_steps=1.0, all_ok=true
- CI loops: many “no-op/cosmetic (AST-equal)” rejections on planner; frequent hardtimeouts on critic_llm
- Fixed PS7-only issue: use ProcessStartInfo.Arguments (not ArgumentList) in run_ci.ps1

**Open items:**
1) Keep strict CI running (30 cycles / 180 min) now that PS5-safe runner is in place
2) Add minimal “coherence” probes to detect real plan delta (avoid AST-equal churn)
3) Investigate critic_llm timeouts (raise per-call timeout / shrink max_tokens / stricter JSON-only prompt)

**Latest session IDs:** see attached ci_session_* and gated_loop_* logs
