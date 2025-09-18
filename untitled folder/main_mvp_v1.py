"""
main_mvp_v1.py — Minimal runnable MVP for CLT–E8 AGI experiments.

What it does
------------
- Generates a small suite of deterministic math tasks.
- Runs two modes: multi_head (12 heads) vs single_head (1 head).
- For each task: simulates a hypothesis, verifies with the Critic, computes a Coherence score,
  commits a SlipState, and logs the attempt.
- Writes two JSON logs under ./experiment_logs/ compatible with experiment_run_schema_v1.json.

How to run
----------
    python main_mvp_v1.py

Files expected in the same folder (or importable via PYTHONPATH):
- workspace_v1.py
- embeddings_v1.py
- critic_v1.py
- tms_lite_v1.py
- logger_v1.py
- tasks_mathcode_v1.py
"""
import os, sys, time, random, math, uuid

# Be resilient to different layouts (same folder or a src/ folder)
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
SRC = os.path.join(HERE, "src")
if os.path.isdir(SRC) and SRC not in sys.path:
    sys.path.insert(0, SRC)

# Try both import styles
try:
    from workspace_v1 import Workspace
    from embeddings_v1 import orthogonal_projections, multihead_project
    from critic_v1 import verify_math, coherence_score, normalize01
    from tms_lite_v1 import TMSLite
    from logger_v1 import RunLogger
    from tasks_mathcode_v1 import gen_tasks
except ImportError:
    from src.workspace_v1 import Workspace
    from src.embeddings_v1 import orthogonal_projections, multihead_project
    from src.critic_v1 import verify_math, coherence_score, normalize01
    from src.tms_lite_v1 import TMSLite
    from src.logger_v1 import RunLogger
    from src.tasks_mathcode_v1 import gen_tasks

def run(mode="multi_head", num_heads=12, seed=42, out_dir="experiment_logs"):
    rnd = random.Random(seed)
    os.makedirs(out_dir, exist_ok=True)
    run_id = f"EXP_{time.strftime('%Y%m%d_%H%M%S')}_{mode}"
    logger = RunLogger(run_id, base_dir=out_dir, config={"heads":num_heads, "mode":mode}, dataset="MathCode")
    ws = Workspace()
    tms = TMSLite()

    # Projection heads (simulate E8-style multi-head memory)
    dim = 32
    mats = orthogonal_projections(dim=dim, num_heads=max(1, num_heads), seed=seed)

    tasks = gen_tasks(n=120, seed=seed+7)

    for t in tasks:
        # Simulated base vector from task; stable across runs
        vec = [ (hash((t["a"],t["b"],t["c"],i)) % 1000)/1000.0 for i in range(dim) ]
        do_slip = (mode != "no_slips")
        heads = multihead_project(vec, mats, theta=0.03, do_slip=do_slip)

        # Produce a hypothesis with mode-dependent noise (multi_head is better on average)
        if t["op"] == "fma":
            truth = t["a"]*t["b"] + t["c"]
        else:
            truth = (t["a"] + t["b"]) * t["c"] - t["a"]
        noise_scale = 0.1 if mode == "multi_head" else 0.3  # multi-head advantage
        hypothesis = truth + rnd.uniform(-noise_scale, noise_scale)

        # Verify
        check = verify_math(t, hypothesis)
        passed = bool(check.get("passed", False))

        # Coherence components (simple proxies):
        # ΔEntropy via inverse-variance across heads
        variances = []
        for h in heads:
            m = sum(h)/len(h)
            v = sum((x-m)**2 for x in h)/len(h)
            variances.append(v)
        inv_var = 1.0 / (1e-6 + sum(variances)/len(variances))
        d_entropy = normalize01(inv_var, 0.0, 100.0)

        # Consistency: multi_head higher (simulated), single_head lower
        consistency = (0.7 + rnd.uniform(0.0, 0.2)) if mode == "multi_head" else (0.4 + rnd.uniform(0.0, 0.2))

        # Contradictions: TMS-lite trivial toggle based on parity; occasional conflict penalties
        key = "toy_parity_key"
        value = (t["a"] + t["b"] + t["c"]) % 2
        conflicts = tms.assert_fact(key, value)
        contradictions = tms.conflict_mass(conflicts) if conflicts else 0.0

        totalC = coherence_score(d_entropy, consistency, contradictions)

        # Commit & log
        sid = ws.commit({"task": t, "hypothesis": hypothesis, "passed": passed},
                        heads=heads, provenance={"mode": mode}, vscore=1.0 if passed else 0.0)
        ws.record_coherence(sid, totalC)

        logger.record_attempt(task_id=t["id"],
                              hypothesis_id=str(uuid.uuid4())[:8],
                              mode=mode,
                              coherence={"d_entropy": d_entropy, "consistency": consistency, "contradictions": contradictions, "total": totalC},
                              retrieval={"k": 0, "supports_found": 0, "supports_required": 0, "heads_consensus": 0.0},
                              contradictions=1 if conflicts else 0,
                              passed=passed,
                              timing_ms=rnd.uniform(5.0, 15.0),
                              slipstate_ids=[sid])

    # Write log
    out_path = os.path.join(out_dir, f"{run_id}.json")
    logger.write(out_path)
    return out_path

if __name__ == "__main__":
    os.makedirs("experiment_logs", exist_ok=True)
    path_multi = run(mode="multi_head", num_heads=12, seed=42, out_dir="experiment_logs")
    path_single = run(mode="single_head", num_heads=1, seed=43, out_dir="experiment_logs")
    print("Wrote logs:\n ", path_multi, "\n ", path_single)
