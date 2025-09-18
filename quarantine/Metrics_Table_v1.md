# Metrics & Thresholds (v1, Ultrathink)
**Date:** 2025-09-10

This file defines **quantified**, **falsifiable** success criteria for the CLT–E8 AGI project. Every experiment must log these metrics and compare against thresholds. When a component is changed, run the **Ablation Battery**.

---

## 1) Core Outcome Metrics

### 1.1 Grounded Correctness (GC)
- **Definition:** Percentage of tasks solved with *Critic*-verified outputs (unit tests / deterministic checks pass).
- **Formula:** `GC = (# passed tasks) / (total tasks)`
- **Thresholds:** **≥ 95%** on curated math+code suites (size ≥ 100 tasks).
- **Notes:** Must use tool-grounding; pure text answers do not count.

### 1.2 Generalization from Demos (GfD)
- **Definition:** After ≤ 5 demonstration trajectories for a new tool/skill, success rate on **unseen** tasks.
- **Protocol:** Provide 3–5 demo traces → hold-out 30+ tasks → measure success.
- **Threshold:** **≥ 80%** success on held-out set.
- **Stability:** 95% bootstrap CI width ≤ 10 pp.

### 1.3 Memory Utility (MU)
- **Definition:** Improvement from enabling **E8 multi-head echo-memory** vs. single-head baseline.
- **Measures:** Accuracy Δ and/or latency Δ.
- **Threshold (pass if any):** **+10% accuracy** *or* **−20% latency**.
- **Protocol:** Same tasks, same seeds; only memory mode toggled.

### 1.4 Contradiction Handling (CH)
- **Definition:** Fraction of detected conflicts automatically resolved via TMS-driven plan revision.
- **Threshold:** **≥ 70%** of conflicts resolved without manual hints.
- **Constraint:** No external edits; internal plan revision only.

### 1.5 Self-Revision Efficacy (SRE)
- **Definition:** On failure, agent proposes and executes a **new** plan with **higher Coherence** that **succeeds**.
- **Threshold:** **≥ 60%** of failures recovered by self-revision.
- **Check:** Coherence(new) > Coherence(old) and Critic passes.

### 1.6 Coherence–Success Correlation (CSC)
- **Definition:** Pearson r between **Coherence score** and success (binary) across runs.
- **Threshold:** **r ≥ 0.60** (p < 0.01).
- **Goal:** Coherence must be predictive of correctness.

---

## 2) Component-Level Metrics

### 2.1 Coherence Components
- **ΔEntropy:** KL(prior → posterior) over belief distribution; normalize to [0,1].
- **Consistency:** Agreement across modules (LLM samples, Symbolic derivations, World Model sims); majority/weighted voting.
- **Contradictions:** Normalized conflict mass from TMS (0 = none; 1 = severe).

**Coherence Score:**  
`C = a·ΔEntropy + b·Consistency − c·Contradictions` with defaults `a=1.0, b=1.2, c=1.5` (see `config/default.yaml`).

### 2.2 Retrieval Robustness (RR)
- **Definition:** Probability that top-k retrieval contains all ground-truth supports.
- **Threshold:** **≥ 90%** at k ≤ 8 with multi-head enabled.
- **Ablation:** Single-head must degrade RR measurably.

### 2.3 Procedural Skill Reliability (PSR)
- **Definition:** Success rate when reusing a stored skill (macro) on novel inputs.
- **Threshold:** **≥ 85%** post-3 successful commitments of the skill.

---

## 3) Ablation Battery (Pass/Fail)

Run each toggle independently, measure GC, MU, RR, CH, SRE, CSC:

1. **Memory Mode:** Multi-head ON ↔ Single-head (baseline).  
   - **Pass:** MU threshold met; RR improves; GC not worse.
2. **Slip Rotations:** On ↔ Off.  
   - **Pass:** With slips ON, CH and SRE improve ≥ 10 pp; CSC increases.
3. **TMS:** On ↔ Off.  
   - **Pass:** CH collapses when Off; with On, CH ≥ 70%.
4. **Critic:** On ↔ Off.  
   - **Pass:** GC significantly worse with Critic Off; CSC drops.
5. **World Model:** On ↔ Off.  
   - **Pass:** Plan selection worsens (lower Coherence; higher runtime) when Off.

A component is **justified** if disabling it **significantly degrades** one or more headline metrics.

---

## 4) Datasets & Protocols

- **Math+Code Suite:** 100–300 deterministic tasks (arithmetic, parsing, CSV transforms).  
- **CSV Analytics Demo:** Rolling z-score per group; outlier flags; plots; explanations.  
- **Tool Learning:** Introduce a new tool (e.g., date parser). Provide 3–5 demos; evaluate on 30+ novel tasks.

**General Protocol:**  
- Fix seeds and configs.  
- Log per-step JSON: goal, hyps, checks, sims, Coherence, outcome, SlipState IDs.  
- Compute metrics with 1,000 bootstrap samples where applicable.

---

## 5) Reporting Format

For each experiment, produce `experiment_logs/run_YYYYMMDD_HHMM.json` and a Markdown report with:

- **Setup:** versions, config, seeds.  
- **Headline Metrics:** GC, GfD, MU, CH, SRE, CSC (+ CIs).  
- **Ablation Table:** per toggle, metric deltas and significance.  
- **Plots:** Coherence vs success; retrieval hit-rate; latency histograms.  
- **Conclusion:** Pass/Fail against thresholds; next actions.

---

## 6) Gates (Promotion Criteria)

- **Week 2 Gate:** Workspace, SlipStates, Critic working; first Coherence logs.  
- **Month 1 Gate:** CSV demo passes GC ≥ 95%; MU threshold met; ablation shows multi-head benefit.  
- **Month 3 Gate:** TMS & World Model integrated; CH ≥ 70%; CSC ≥ 0.6.  
- **Month 6 Gate:** Few-shot tool learning GfD ≥ 80%; PSR ≥ 85%; publish internal ablation report.

---

## 7) Sanity Checks

- No in-place mutation of SlipStates; provenance required.  
- Average chars/word in generated code/text: 3.0–6.5.  
- Tests must be deterministic; random seeds fixed.  
- All external writes OFF unless explicitly authorized.

---

**This Metrics Table is binding.** If a change improves one metric but degrades another, we log trade-offs and decide explicitly in the Master Instructions.
