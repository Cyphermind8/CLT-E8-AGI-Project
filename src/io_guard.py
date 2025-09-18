Set-Location C:\AI_Project

$purePython = @'
from __future__ import annotations
from typing import Any
from .governor import Governor, GovernorConfig

_G = Governor(GovernorConfig.from_env())

def write_text(path: str, text: str) -> None:
    _G.write_text(path, text)

def append_text(path: str, text: str) -> None:
    _G.append_text(path, text)

def write_json(path: str, obj: Any, sort_keys: bool = True, indent: int = 2) -> None:
    _G.write_json(path, obj, sort_keys=sort_keys, indent=indent)

def copy_file(src: str, dst: str) -> None:
    _G.copy_file(src, dst)

def approved_targets() -> list[str]:
    return _G.approved_targets()
'@

# Hard overwrite with ONLY the Python above
Set-Content .\src\io_guard.py $purePython -Encoding utf8
