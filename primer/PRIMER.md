## PROJECT SEED (evergreen)
Navigator Primer — CLT-E8
Mode: Default = concise; “Ultrathink” on request.
Machine: Windows + PowerShell; Python 3.10; Local OpenAI-compatible server at http://localhost:1234/v1 (unless specified).
Non-negotiables:
- No async promises. All work is done in-message.
- Prefer small, testable increments + ablations. Always include rollback.
- Provide complete files in one fenced block (# FILE: path). No fragments.
- Run instructions must be Windows-friendly with expected outputs.
- Tests first; metrics logged to ai_performance_log.json.
- Safety gates: preflight (pytest), AST function-set parity, backups to ./backup/, tiny patch budget.
Key artifacts:
- ai_self_modification.py (orchestrator)
- gated_loop.py (micro-transform loop)
- ai_performance_log.json (metrics + modifications)
- scripts/ (tooling)


## RUN SEED (recent deltas)
Recent Deltas — last modifications
- 2025-09-16T17:39:49.882038Z | cycle=1 | applied=False | target=rotating candidates | [CYCLE 1] starting...
- 2025-09-16T17:39:49.884120Z | cycle=2 | applied=False | target=rotating candidates | [CYCLE 2] starting...
- 2025-09-17T07:15:46.663187Z | cycle=0 | applied=False | target=ai_core.py | [CYCLE 0] starting...
- 2025-09-17T07:16:55.833393Z | cycle=0 | applied=False | target=ai_core.py | [CYCLE 0] starting...
- 2025-09-17T07:25:06.754045Z | cycle=0 | applied=False | target=ai_core.py | [CYCLE 0] starting...
- 2025-09-17T07:32:16.740272Z | cycle=0 | applied=False | target=ai_core.py | [CYCLE 0] starting...
- 2025-09-17T07:38:24.343143Z | cycle=0 | applied=False | target=code_analysis.py | [CYCLE 0] starting...
- 2025-09-17T07:38:41.404889Z | cycle=0 | applied=False | target=rotating candidates | [CYCLE 0] starting...
- 2025-09-17T07:38:41.407889Z | cycle=1 | applied=False | target=rotating candidates | [CYCLE 1] starting...
- 2025-09-17T07:38:41.420230Z | cycle=2 | applied=False | target=rotating candidates | [CYCLE 2] starting...

Canary metric: accepted=0 window=23 rate=0.0% (last 50 modifications)


## ASK SEED (fill these before pasting)
Current Ask (fill before starting a new chat):
- Objective:
- Constraints (token/time/tools):
- Inputs to consider (files/paths):
- Decision needed now:
