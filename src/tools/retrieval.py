# FILE: src/tools/retrieval.py
from __future__ import annotations
from pathlib import Path
import math, re
from collections import Counter, defaultdict
from typing import List, Tuple

TOKEN = re.compile(r"[A-Za-z0-9_]+")

def _tok(s: str) -> list[str]:
    return [t.lower() for t in TOKEN.findall(s)]

class MiniLexicalIndex:
    def __init__(self, root: Path):
        self.docs: list[tuple[str, list[str]]] = []
        self.df = Counter()
        for p in sorted(root.glob("**/*.md")):
            text = p.read_text(encoding="utf-8", errors="ignore")
            toks = _tok(text)
            self.docs.append((str(p), toks))
            for w in set(toks): self.df[w]+=1
        self.N = max(1, len(self.docs))

    def search(self, query: str, k: int = 3) -> list[tuple[str, float, str]]:
        q = _tok(query)
        if not q: return []
        idf = {w: math.log((self.N+1)/(1+self.df.get(w,0))) for w in set(q)}
        scores = []
        for path, toks in self.docs:
            tf = Counter(toks)
            score = sum((tf.get(w,0)) * idf.get(w,0.0) for w in q)
            if score>0: scores.append((path, score))
        scores.sort(key=lambda x: x[1], reverse=True)
        out=[]
        for path,score in scores[:k]:
            text = Path(path).read_text(encoding="utf-8", errors="ignore")
            out.append((path, float(score), text[:500]))
        return out