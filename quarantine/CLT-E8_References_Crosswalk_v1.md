# CLT–E8 References Cross‑Walk (v1)
**Date:** 2025-09-10

This document binds the **CLT–E8 Evolved** paper to the **Theory Mapping (v1)**, **Master Instructions**, and **Metrics_Table_v1**.
For each major equation/claim in the paper, we specify: (A) software implementation, (B) validation metric(s), and (C) roadmap milestone(s).
If an item lacks at least one of A/B/C, it is considered **un-grounded** and must not gate project decisions.

---

## Legend
- **Paper** → section/equation/claim in _CLT–E8 Evolved.txt_.
- **Mapping** → section in _CLT–E8 → AGI Theory Mapping (v1)_.
- **Metrics** → identifiers from _Metrics_Table_v1.md_.
- **Milestones** → Master Instructions roadmap gates.

---

## 1) Coherence Integral
- **Paper:** Coherence defined by overlap integral \(\mathcal{C} = \int \psi_1^*\psi_2\,dV\) (foundation for memory and stability).
- **Mapping:** §2.1 Coherence → `critic.coherence_score(ΔEntropy, Consistency, Contradictions)`; Workspace ledger.
- **Metrics:** CSC (Coherence–Success Correlation ≥ 0.6), GC (≥95% on curated suites), CH (≥70% resolved), SRE (≥60% recovery).
- **Milestones:** Month‑1 (planner ranks by Coherence), Month‑3 (CSC ≥ 0.6).

## 2) Phase Slips as Topological Memory
- **Paper:** Phase slips encode robust invariants (Chern‑like); memory is physics‑level persistent.
- **Mapping:** §2.2 SlipStates (immutable DAG nodes); commit‑only writes; provenance.
- **Metrics:** MU (+10% accuracy or −20% latency vs single‑head), RR (≥90% top‑k hit rate), GC.
- **Milestones:** Week‑2 (Workspace + SlipState ledger), Month‑1 (demo uses committed SlipStates).

## 3) Slip Operator \(\hat{S}_i = e^{i\theta_i T_{\alpha_i}}\) → Phase‑Gated Attention
- **Paper:** Slip operators suppress mirror states; select stable chirality.
- **Mapping:** §2.3 Embedding phase rotations during write/read; contradiction‑driven phase penalties.
- **Metrics:** CH (≥70%), SRE (≥60%), CSC ↑ when slips enabled; Ablation “Slip Rotations” must degrade results when Off.
- **Milestones:** Month‑1 (basic slips wired), Month‑3 (slip penalties integrated with TMS).

## 4) E8 Lattice / Topological QEC Substrate
- **Paper:** E8 root system provides rich orthogonal structure; supports non‑local redundancy akin to QEC.
- **Mapping:** §2.4 Multi‑head embeddings (8–16 heads), consensus retrieval (intersection across heads).
- **Metrics:** MU (pass), RR (≥90%), GC stable or improved; Ablation “Memory Mode: Multi‑head→Single‑head” must show degradation.
- **Milestones:** Month‑1 (E8 multi‑head retrieval in demo).

## 5) Tanh Potential \(V(\mathcal{C}) = \Lambda(1 - \tanh(k\,\mathcal{C}))^2\)
- **Paper:** RG‑motivated potential yielding saturation/stability.
- **Mapping:** §2.5 Planner exploration gate g = tanh(k·uncertainty); `config/default.yaml:tanh_k`.
- **Metrics:** CSC ↑ post‑integration; improved stability (lower contradiction mass) at equivalent success.
- **Milestones:** Month‑3 (tanh gate on planner).

## 6) RG Flow / UV Stability
- **Paper:** Multi‑loop RG yields bounded couplings; UV completion avoids divergences.
- **Mapping:** §2.6 Learning‑rate caps; confidence growth limits; embedding norm regularization; verification‑gated weight increases.
- **Metrics:** Stability: fewer runaways; CH improves; CSC stable; report variance bounds in experiment logs.
- **Milestones:** Ongoing; documented in Experiment_Design and config changes.

## 7) Chirality Selection (Mirror Suppression)
- **Paper:** Dynamic slips phase out mirror fermions in E8 → SM decomposition.
- **Mapping:** §2.7 Analogue: beliefs repeatedly contradicted receive cumulative phase penalties → retrieval weight decays.
- **Metrics:** CH (contradictions decline across episodes), SRE (recoveries increase), CSC ↑.
- **Milestones:** Month‑6 (belief revision loop mature).

## 8) Quantum Error Correction Analogy
- **Paper:** E8 lattice supports topological QEC; slips enable non‑local correction operations.
- **Mapping:** Redundant multi‑head encodings; consensus reads; procedural skills stored with redundancy and provenance.
- **Metrics:** Error‑rate reduction ≥20% with consensus vs single‑head; RR ≥90% at k≤8.
- **Milestones:** Month‑3 ablation report demonstrating consensus benefit.

## 9) Observational Predictions → Software Stress Tests
- **Paper:** (a) GW echoes (kHz, ~10–30 ms), (b) Casimir drift (ppm), (c) PTA modulations (∼1%).
- **Mapping:** Long‑trace memory stability tests and micro‑drift analyses: measure Coherence drift across repeated runs; persistence of retrieval echo under perturbation.
- **Metrics:** CSC stability across long runs; MU maintained; drift bounded (specify in Experiment Design).
- **Milestones:** Month‑6 extended‑run stress suite.

## 10) Falsifiability & Reproducibility
- **Paper:** Bold claims must be falsifiable; predictions logged with confidence.
- **Mapping:** Ablation Battery (§5 of Metrics) and deterministic test harness; per‑run JSON logs (goal, hyps, checks, sims, Coherence, outcomes, SlipState IDs).
- **Metrics:** All headline metrics computed with CIs; pass/fail vs thresholds.
- **Milestones:** Month‑1 first ablation; Month‑3 comprehensive ablation battery.

---

## Cross‑Checks (Integrity Rules)
- Each Paper claim must map to **at least one** Mapping section **and** a Metric.  
- No new Mapping feature is “done” without a **Metric** and an **ablation**.  
- Any Roadmap milestone must reference at least one Paper claim (or be labeled “engineering only”).

---

## Open Items to Resolve in v2
- Numerical bounds for “drift” metrics in long‑horizon runs (tie to Casimir/PTA analogues).  
- Formal definition/estimator of ΔEntropy component for heterogeneous tasks.  
- Evidence thresholds to commit a SlipState (how many checks/sources?).  
- Robust head‑construction method: analytical vs. learned orthogonal projections.
