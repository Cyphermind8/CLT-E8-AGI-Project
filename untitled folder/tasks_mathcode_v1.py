"""
tasks_mathcode_v1.py — Generates simple deterministic math tasks.
Each task includes integers a, b, c and an op ('fma' or 'mix') with known ground-truth.
Use with critic_v1.verify_math for deterministic checking.
"""
from typing import List, Dict
import random

def gen_tasks(n: int = 100, seed: int = 123) -> List[Dict]:
    """Generate n deterministic tasks using an internal PRNG seed.
    Returns a list of dicts: {id, a, b, c, op}
    """
    rnd = random.Random(seed)
    tasks = []
    for i in range(n):
        a = rnd.randint(-50, 50)
        b = rnd.randint(-50, 50)
        c = rnd.randint(-50, 50)
        op = 'fma' if rnd.random() < 0.5 else 'mix'
        tasks.append({"id": f"math_{i:03d}", "a": a, "b": b, "c": c, "op": op})
    return tasks
