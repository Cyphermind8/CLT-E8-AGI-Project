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
