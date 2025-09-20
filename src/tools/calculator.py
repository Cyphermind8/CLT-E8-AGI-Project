# FILE: src/tools/calculator.py
from __future__ import annotations
import ast, operator

# Safe arithmetic / bitwise operators only
OPS_BIN = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.LShift: operator.lshift,
    ast.RShift: operator.rshift,
    ast.BitOr: operator.or_,     # note: or_ (underscore), not "or"
    ast.BitAnd: operator.and_,   # and_ (underscore)
    ast.BitXor: operator.xor,
}
OPS_UN = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

def eval_expr(expr: str) -> float | int:
    """
    Evaluate a simple arithmetic/bitwise expression safely:
    +, -, *, /, //, %, **, <<, >>, |, &, ^, unary +/-
    """
    node = ast.parse(expr, mode="eval")
    return _eval(node.body)

def _eval(n):
    # Numeric literals
    if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
        return n.value
    if isinstance(n, ast.Num):  # Py3.8 compat
        return n.n
    # Binary ops
    if isinstance(n, ast.BinOp) and type(n.op) in OPS_BIN:
        return OPS_BIN[type(n.op)](_eval(n.left), _eval(n.right))
    # Unary ops
    if isinstance(n, ast.UnaryOp) and type(n.op) in OPS_UN:
        return OPS_UN[type(n.op)](_eval(n.operand))
    # Parenthesized
    if isinstance(n, ast.Expression):
        return _eval(n.body)
    raise ValueError(f"Unsupported or unsafe expression: {ast.dump(n, include_attributes=False)}")