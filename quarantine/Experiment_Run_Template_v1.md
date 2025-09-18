# Experiment Run Template (v1)
**Date:** 2025-09-10
**Run ID:** EXP_{YYYYMMDD_HHMM}

---

## 1. Setup

- **Code Version:** (git hash / file versions)
- **Config:** (`config/default.yaml` snapshot)
- **Seeds:** (random seeds fixed)
- **Dataset:** (Math+Code suite / CSV demo / Retrieval toy / Contradiction toy)
- **Hardware:** (CPU/GPU, RAM)
- **Notes:** (context, changes since last run)

---

## 2. Goal

- **Task:** (e.g., rolling z-score per group)
- **Hypothesis:** (e.g., multi-head memory improves retrieval robustness)

---

## 3. Metrics Collected

- **Grounded Correctness (GC):** X / N = Y% (Target ≥ 95%)
- **Generalization from Demos (GfD):** X / N = Y% (Target ≥ 80%)
- **Memory Utility (MU):** Δ Accuracy = …, Δ Latency = … (Target +10% or −20%)
- **Contradiction Handling (CH):** Resolved / Injected = …% (Target ≥ 70%)
- **Self-Revision Efficacy (SRE):** Recovered / Failures = …% (Target ≥ 60%)
- **Coherence–Success Correlation (CSC):** r = …, p = … (Target ≥ 0.6)

---

## 4. Ablation Results

| Mode                  | GC   | MU   | CH   | SRE  | CSC  | Notes |
|-----------------------|------|------|------|------|------|-------|
| Full system           |      |      |      |      |      |       |
| Single-head memory    |      |      |      |      |      |       |
| No slip rotations     |      |      |      |      |      |       |
| No TMS                |      |      |      |      |      |       |
| No Critic             |      |      |      |      |      |       |
| No World Model        |      |      |      |      |      |       |

---

## 5. Logs

- **SlipStates committed:** (IDs, hashes)
- **Sample Coherence ledger:**  
  (state_id, ΔEntropy, Consistency, Contradictions, total C)

- **Runtime stats:** (latency, memory)

---

## 6. Plots

- [ ] Coherence vs Success scatter
- [ ] Retrieval robustness histograms
- [ ] Ablation deltas

---

## 7. Conclusion

- **Thresholds met?** (list which metrics hit targets)
- **Milestone satisfied?** (Week‑2 / Month‑1 / Month‑3 gate)
- **Next actions:** (tuning, new dataset, new module)

---

## 8. Attachments

- Config file snapshot
- Dataset / task IDs
- Logs JSON (goal, hyps, checks, sims, Coherence, outcomes)
