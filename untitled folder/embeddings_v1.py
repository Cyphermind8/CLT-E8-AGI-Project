"""
embeddings_v1.py — E8-inspired multi-head projections with simple slip rotations.
- Deterministic pseudo-random projection matrices based on a seed.
- Cosine similarity utilities for retrieval (future use).
- Slip rotation approximates a tiny phase-like transform to enable gating.
"""
import math, random
from typing import List

def _seed_rng(seed: int) -> random.Random:
    rnd = random.Random()
    rnd.seed(seed)
    return rnd

def orthogonal_projections(dim: int = 32, num_heads: int = 12, seed: int = 42) -> List[List[List[float]]]:
    """Return a list of projection matrices (dim x dim) for each head.
    NOTE: For MVP these are random matrices, not strictly orthogonal. Good enough to test multi-head behavior.
    """
    rnd = _seed_rng(seed)
    mats = []
    for _ in range(num_heads):
        mat = [[rnd.uniform(-1.0, 1.0) for _ in range(dim)] for _ in range(dim)]
        mats.append(mat)
    return mats

def project(vec: List[float], mat: List[List[float]]) -> List[float]:
    """Multiply vector by matrix (row-major)."""
    out = [0.0]*len(vec)
    for i, row in enumerate(mat):
        s = 0.0
        for j, v in enumerate(vec):
            s += row[j]*v
        out[i] = s
    return out

def l2(x: List[float]) -> float:
    return math.sqrt(sum(v*v for v in x)) + 1e-9

def cosine(a: List[float], b: List[float]) -> float:
    return sum(x*y for x,y in zip(a,b)) / (l2(a)*l2(b))

def slip_rotate(head_vec: List[float], theta: float = 0.05) -> List[float]:
    """Apply a tiny 'phase-like' rotation by mixing with a shifted copy of the vector."""
    if not head_vec:
        return head_vec
    rotated = []
    c = math.cos(theta)
    s = math.sin(theta)
    for i, v in enumerate(head_vec):
        v_next = head_vec[(i+1) % len(head_vec)]
        rotated.append(c*v - s*v_next)
    return rotated

def multihead_project(vec: List[float], mats: List[List[List[float]]], theta: float = 0.05, do_slip: bool = True) -> List[List[float]]:
    """Project a base vector through all heads; optionally apply slip rotations."""
    heads = []
    for mat in mats:
        h = project(vec, mat)
        heads.append(slip_rotate(h, theta) if do_slip else h)
    return heads
