"""
main_v1.py — Control loop wiring modules together (dry-run stub).
"""
from src.workspace_v1 import Workspace
from src.embeddings_v1 import project_multihead, slip_rotate
from src.symbolic_v1 import TMS
from src.world_model_v1 import rollout
from src.planner_v1 import plan
from src.critic_v1 import verify, coherence_score

def run():
    ws = Workspace()
    tms = TMS()
    # Example vector
    vec = [0.1, 0.2, 0.3]
    heads = [slip_rotate(h) for h in project_multihead(vec, 12)]
    sid = ws.commit({"example": True}, heads, provenance={"demo":"init"}, vscore=0.0)
    facts = {"foo":"bar"}
    checks = verify(facts)
    sims = rollout({"steps":["demo"]})
    coh = coherence_score(0.2, 0.8, 0.0)
    ws.record_coherence(sid, coh)
    print("Committed state:", sid, "Coherence:", coh, "Checks:", checks, "Sims:", sims)

if __name__ == "__main__":
    run()
