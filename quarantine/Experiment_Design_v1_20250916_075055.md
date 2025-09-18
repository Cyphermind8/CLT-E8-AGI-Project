# Experiment Design (v1)

## Datasets / Tasks
- **CSV Analytics**: Rolling z-score per group, outlier flagging, plotting.
- **Math+Code**: Deterministic unit-testable problems (arithmetic, data transforms).

## Protocol
1. Seed episodic traces with a few demonstrations (≤5) per tool.
2. Run test episodes with and without multi-head memory (ablation).
3. Collect Coherence scores, Critic pass/fail, TMS conflicts.
4. Compute metrics (see Metrics_Table_v1.md).

## Logging
- Write per-step JSON logs to `experiment_logs/`:
  - goal, hypotheses, checks, sims, Coherence, outcome, slipstate IDs.
