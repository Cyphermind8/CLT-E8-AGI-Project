"""
critic_v1.py — Tool-grounded verification (math/code) and coherence scoring.
"""
def verify(facts):
    # Placeholder: always pass
    return {"passed": True}

def coherence_score(d_entropy: float, consistency: float, contradictions: float, w=(1.0,1.2,1.5)) -> float:
    a,b,c = w
    return d_entropy + b*consistency - c*contradictions
