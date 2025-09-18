# Coherence probes (AST + token delta)
from __future__ import annotations
import ast, hashlib, re
from typing import Tuple, Dict

def _strip_docstrings(node: ast.AST) -> ast.AST:
    for n in ast.walk(node):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            if getattr(n, "body", None):
                first = n.body[0]
                if isinstance(first, ast.Expr) and isinstance(getattr(first, "value", None), ast.Constant) and isinstance(first.value.value, str):
                    n.body = n.body[1:]
    return node

def _zero_constants(node: ast.AST) -> ast.AST:
    for n in ast.walk(node):
        if isinstance(n, ast.Constant):
            if isinstance(n.value, (str, int, float, complex, bytes)):
                n.value = type(n.value)()
    return node

def ast_signature(code_text: str) -> Tuple[str, Dict[str,int]]:
    try:
        t = ast.parse(code_text)
    except SyntaxError:
        return ("<SYNTAX_ERROR>", {})
    t = _strip_docstrings(t)
    t = _zero_constants(t)
    nodetypes = {}
    for n in ast.walk(t):
        k = type(n).__name__
        nodetypes[k] = nodetypes.get(k, 0) + 1
    digest = hashlib.sha256(ast.dump(t, annotate_fields=False).encode("utf-8")).hexdigest()
    return (digest, nodetypes)

def semantic_delta(before: str, after: str) -> float:
    def toks(s: str):
        s = re.sub(r"#.*", "", s)
        s = re.sub(r'"""(?:.|\\n)*?"""|\'\'\'(?:.|\\n)*?\'\'\'', "", s)
        s = re.sub(r'\\s+', " ", s)
        return [t for t in re.split(r"[^A-Za-z0-9_]+", s) if t]
    a, b = set(toks(before)), set(toks(after))
    if not a and not b: return 0.0
    inter = len(a & b); union = len(a | b)
    jaccard = inter / max(union, 1)
    return 1.0 - jaccard

def coherence_score(before: str, after: str) -> float:
    sig_a, _ = ast_signature(before)
    sig_b, _ = ast_signature(after)
    if sig_a == "<SYNTAX_ERROR>" or sig_b == "<SYNTAX_ERROR>":
        return 0.0
    ast_change = 0.0 if sig_a == sig_b else 0.5
    sem = semantic_delta(before, after)
    return max(0.0, min(1.0, 0.4*ast_change + 0.6*sem))
