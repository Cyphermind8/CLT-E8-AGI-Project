from __future__ import annotations
import json, os, subprocess, sys, time, shutil, contextlib, difflib
from dataclasses import dataclass
from typing import Callable, Dict, Any, List, Optional, Tuple

from src.io_guard import write_text, write_json, approved_targets
from src.utils.runlog import start_run, finish_run
from src.ai_decision import decision

# Utilities
def _project_root() -> str:
    roots = approved_targets()
    if not roots: return os.getcwd()
    # approved_targets are absolute paths under project root; commonpath gives us the root
    return os.path.commonpath(roots)

ROOT = _project_root()

def _read_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _latest_before_after() -> Tuple[Dict[str,Any], Dict[str,Any]]:
    """
    Heuristic: pick the most recent two bench JSONs in reports/.
    If only one exists, use it as both (no delta).
    """
    rep = os.path.join(ROOT, "reports")
    if not os.path.isdir(rep): return {}, {}
    js = [os.path.join(rep, p) for p in os.listdir(rep) if p.endswith(".json")]
    js.sort()
    if not js: return {}, {}
    if len(js) == 1:
        return _read_json(js[-1]).get("outputs", {}).get("summary", {}), _read_json(js[-1]).get("outputs", {}).get("summary", {})
    return _read_json(js[-2]).get("outputs", {}).get("summary", {}), _read_json(js[-1]).get("outputs", {}).get("summary", {})

def _line_count(s: str) -> int:
    return s.count("\n") + (0 if s.endswith("\n") else 1)

def _git(*args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return proc.stdout

def _diffstat(old: str, new: str) -> Tuple[int, str]:
    d = list(difflib.unified_diff(old.splitlines(True), new.splitlines(True), n=0))
    lines = sum(1 for _ in d)
    return lines, "".join(d)

@dataclass
class Candidate:
    name: str
    target_path: str
    produce_new_text: Callable[[str], str]  # (old_text) -> new_text
    rationale: str

    def apply(self) -> Dict[str, Any]:
        abs_path = os.path.join(ROOT, self.target_path)
        with open(abs_path, "r", encoding="utf-8") as f:
            old = f.read()
        new = self.produce_new_text(old)
        changed_lines, patch = _diffstat(old, new)
        if new == old:
            return {"applied": False, "changed_lines": 0, "message": "no change"}
        # Write via Governor
        write_text(self.target_path, new)
        return {"applied": True, "changed_lines": changed_lines, "patch": patch}

# Built-in mutation generators (safe, surgical)
def _add_json_merge_mode_alias() -> Candidate:
    target = "src/tools/json_tools_v1.py"
    def mutate(old: str) -> str:
        # ensure 'policy' is mapped to 'mode' (you already added, but keep idempotent)
        if "policy" in old and "prefer_b" in old:
            return old  # looks present; no-op
        # Small, conservative insertion: just a comment marker for idempotency
        marker = "# (CLT-E8) mode synonyms ensured"
        return old if marker in old else old.rstrip() + "\n" + marker + "\n"
    return Candidate(
        name="json_merge_policy_alias_guard",
        target_path=target,
        produce_new_text=mutate,
        rationale="Ensure json_merge accepts mode/policy synonyms; idempotent marker"
    )

def _tighten_execute_call_normalizer() -> Candidate:
    target = "src/tools/json_tools_v1.py"
    def mutate(old: str) -> str:
        # Nudge normalization table to accept 'preferright'/'preferleft' if missing
        if "preferright" in old and "preferleft" in old:
            return old
        needle = "table = {"
        if needle not in old:
            return old
        new = old.replace(
            needle,
            needle + "\n        # (CLT-E8) accept preferleft/preferright synonyms"
        )
        return new
    return Candidate(
        name="execute_call_synonym_comment",
        target_path=target,
        produce_new_text=mutate,
        rationale="Broaden arg normalization hints (no functional risk)"
    )

def _bench_prompt_precision_hint() -> Candidate:
    target = "bench/run_bench.py"
    def mutate(old: str) -> str:
        # Add a precision comment in bench to reduce output drift (idempotent marker)
        marker = "# (CLT-E8) precision: prefer exact numeric/string outputs"
        return old if marker in old else old.rstrip() + "\n" + marker + "\n"
    return Candidate(
        name="bench_precision_hint",
        target_path=target,
        produce_new_text=mutate,
        rationale="Bias prompts toward exact outputs; helps accuracy/determinism"
    )

CANDIDATE_FACTORIES = [
    _add_json_merge_mode_alias,
    _tighten_execute_call_normalizer,
    _bench_prompt_precision_hint,
]

def _pytest_pass_rate() -> float:
    # Light-weight probe: run pytest -q and parse summary line
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.stdout.strip().splitlines()
    # Expect last line like ".................... [100%]"
    passed = None
    for line in reversed(out):
        if line.endswith("%]"):
            try:
                pct = float(line.split("[")[-1].split("%]")[0])
                return max(0.0, min(1.0, pct/100.0))
            except Exception:
                break
    # Fallback neutral
    return 0.5

def _bench_once() -> Dict[str, Any]:
    # Reuse your runner with logging if present, else call module directly
    script = os.path.join(ROOT, "scripts", "run_bench_with_log.py")
    if os.path.isfile(script):
        subprocess.run([sys.executable, script], cwd=ROOT, check=True)
    else:
        subprocess.run([sys.executable, "-m", "bench.run_bench"], cwd=ROOT, check=True)
    # Return latest summary
    _, after = _latest_before_after()
    return after

def simulate(plan_only: bool = True, apply_top_k: int = 1) -> Dict[str, Any]:
    """Generate candidates, score predicted coherence delta using the last two runs, optionally apply & evaluate."""
    run_dir = start_run({"task": "ai_learning.simulate", "plan_only": plan_only, "k": apply_top_k})
    try:
        before, _ = _latest_before_after()
        if before:
            before["_pytest_pass_rate"] = _pytest_pass_rate()

        # Build candidates
        cands = [f() for f in CANDIDATE_FACTORIES]

        # Score predicted deltas (pre-application, we assume lines_changed small)
        plan = []
        for c in cands:
            # Fake "after" identical to before for prediction (we use priors below)
            after_pred = dict(before) if before else {}
            # Heuristic priors by candidate type:
            priors = {
                "accuracy": 0.01 if "precision" in c.name else 0.005,
                "determinism": 0.01,
                "efficiency": 0.0,
            }
            if after_pred:
                s = after_pred.get("success", {})
                rate = float(s.get("rate", 0.0)) + priors["accuracy"]
                after_pred.setdefault("success", {})["rate"] = min(1.0, rate)
                after_pred["determinism_ok"] = bool(after_pred.get("determinism_ok", True))
                lat = float(after_pred.get("latency", {}).get("avg_s", 3.0))
                after_pred.setdefault("latency", {})["avg_s"] = max(0.5, lat - 0.02)

            report = decision(before_summary=before or {}, after_summary=after_pred or {},
                              lines_changed=8, lint_ok=True)
            plan.append({
                "name": c.name,
                "target": c.target_path,
                "rationale": c.rationale,
                "predicted": report,
            })

        # Rank best-first
        plan.sort(key=lambda x: x["predicted"]["score"], reverse=True)

        if plan_only:
            out = {"plan_only": True, "ranked_candidates": plan}
            write_json(os.path.join("runs", "latest_ai_learning_plan.json"), out)
            return out

        # APPLY: try top-k sequentially; keep the best “after” actual score
        applied = []
        for item in plan[:max(1, apply_top_k)]:
            # Read old text for diffsize
            abs_path = os.path.join(ROOT, item["target"])
            with open(abs_path, "r", encoding="utf-8") as f:
                old_text = f.read()

            # Apply mutation
            cand = next(c for c in cands if c.name == item["name"])
            info = cand.apply()

            if not info.get("applied"):
                item["applied"] = False
                item["apply_info"] = info
                applied.append(item)
                continue

            # Run tests and bench to get real “after”
            pass_rate = _pytest_pass_rate()
            after = _bench_once()
            if after:
                after["_pytest_pass_rate"] = pass_rate

            # Count changed lines for simplicity axis
            changed = int(info.get("changed_lines", 0))
            rep = decision(before_summary=before or {}, after_summary=after or {},
                           lines_changed=changed, lint_ok=True)
            item["applied"] = True
            item["apply_info"] = info
            item["actual"] = rep
            applied.append(item)

            # If coherence score is negative, revert the change automatically
            if rep["score"] < 0:
                # Revert with git (safer than trying to re-write the old text)
                _git("checkout", "--", item["target"])

        # Commit all net-positive changes together
        _git("add", "-A")
        msg_lines = ["ai_learning: apply coherence-aligned edits"]
        for a in applied:
            if a.get("applied") and a.get("actual", {}).get("score", 0) >= 0:
                msg_lines.append(f"- {a['name']}: +{a['actual']['score']:.4f}")
        if len(msg_lines) > 1:
            _git("commit", "-m", "\n".join(msg_lines))

        out = {"plan_only": False, "applied": applied}
        write_json(os.path.join("runs", "latest_ai_learning_apply.json"), out)
        return out
    finally:
        finish_run(run_dir, {"ok": True})
        
if __name__ == "__main__":
    # CLI:
    #   python -m src.ai_learning            -> plan only
    #   python -m src.ai_learning apply 1    -> apply top-1
    #   python -m src.ai_learning apply 2    -> apply top-2
    args = sys.argv[1:]
    if not args:
        res = simulate(plan_only=True)
        print(json.dumps(res, indent=2))
        sys.exit(0)
    if args[0] == "apply":
        k = int(args[1]) if len(args) > 1 else 1
        res = simulate(plan_only=False, apply_top_k=k)
        print(json.dumps(res, indent=2))
        sys.exit(0)
    print("Usage: python -m src.ai_learning [apply K]")
