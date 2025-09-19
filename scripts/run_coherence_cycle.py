import os, sys

# Ensure the project root is on sys.path no matter where we launch from
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.ai.ai_learning import load_learning_state, save_learning_state, apply_mutations
from src.ai.ai_decision import propose_mutations
from src.utils.runlog import runlog
from src.io_guard import write_json

def main():
    state = load_learning_state()
    with runlog({"runner": "coherence_cycle"}) as rd:
        mutations = propose_mutations(state)
        new_state, summary = apply_mutations(state, mutations)
        save_learning_state(new_state)
        # record a per-run summary so we can inspect later in runs/<rid>/
        write_json(str((rd / "coherence_summary.json")), summary)

if __name__ == "__main__":
    main()
