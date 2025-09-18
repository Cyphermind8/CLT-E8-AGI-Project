from __future__ import annotations
import ast

def syntax_ok(code_text: str) -> bool:
    try:
        ast.parse(code_text)
        return True
    except SyntaxError:
        return False
