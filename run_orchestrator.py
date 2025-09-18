# FILE: run_orchestrator.py
#!/usr/bin/env python3
from __future__ import annotations
import ai_self_modification as orch

if __name__ == "__main__":
    # Edit this argv list any time you want different flags
    orch.main(['--cycles','1','--strict','--no-preflight','--path','ai_core.py'])
