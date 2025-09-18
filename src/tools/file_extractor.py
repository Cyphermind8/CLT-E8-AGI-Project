# FILE: src/tools/file_extractor.py
from __future__ import annotations
import argparse, dataclasses, hashlib, json, os, re, shutil, sys, tempfile, time
from typing import List, Optional, Tuple

# Fenced:  ```python\n# FILE: path\n<body>\n```
_FENCED = re.compile(
    r"```(?:[a-zA-Z0-9_+\-]*\n)?#\s*FILE:\s*(?P<path>[^\r\n]+)\r?\n(?P<body>.*?)(?:```|\Z)",
    re.DOTALL | re.MULTILINE,
)
# Unfenced:  ^# FILE: path\n<body>(?=^# FILE:|\Z)
_UNFENCED = re.compile(
    r"^#\s*FILE:\s*(?P<path>[^\r\n]+)\r?\n(?P<body>.*?)(?=^#\s*FILE:|\Z)",
    re.DOTALL | re.MULTILINE,
)

def _ts() -> str: return time.strftime("%Y%m%d_%H%M%S", time.localtime())

@dataclasses.dataclass
class WriteItem:
    rel_path: str
    abs_path: str
    content: bytes
    backup_path: Optional[str] = None

@dataclasses.dataclass
class Plan:
    workspace_root: str
    items: List[WriteItem]
    def describe(self) -> str:
        lines = [f"Plan: {len(self.items)} file(s)"]
        for it in self.items:
            h = hashlib.md5(it.content).hexdigest()
            lines.append(f"  - {it.rel_path} ({len(it.content)} bytes, md5={h})")
        return "\n".join(lines)
    def apply(self) -> None:
        os.makedirs(os.path.join(self.workspace_root, "backup"), exist_ok=True)
        for it in self.items:
            os.makedirs(os.path.dirname(it.abs_path), exist_ok=True)
            if os.path.exists(it.abs_path):
                rel_sanitized = it.rel_path.replace(":", "").replace("\\", "_").replace("/", "_")
                it.backup_path = os.path.join(self.workspace_root, "backup", f"{rel_sanitized}_{_TS()}.bak")
                shutil.copy2(it.abs_path, it.backup_path)
            fd, tmp = tempfile.mkstemp(prefix=".tmp_write_", dir=os.path.dirname(it.abs_path))
            try:
                with os.fdopen(fd, "wb") as f: f.write(it.content)
                os.replace(tmp, it.abs_path)
            finally:
                try:
                    if os.path.exists(tmp): os.remove(tmp)
                except Exception:
                    pass

def _TS() -> str: return _ts()

class MultiFileExtractor:
    """
    Extracts (path, body) pairs from text containing one or more '# FILE:' blocks.
    Accepts fenced or unfenced forms. Preserves match order.
    """
    def __init__(self, workspace_root: str, allowed_subpaths: Optional[List[str]] = None):
        self.workspace_root = os.path.abspath(workspace_root)
        self.allowed_subpaths = [self.workspace_root] if not allowed_subpaths else [os.path.abspath(p) for p in allowed_subpaths]

    @staticmethod
    def detect(text: str) -> bool:
        return "# FILE:" in text or "# file:" in text.lower()

    def _normalize_rel(self, rel_path: str) -> str:
        rp = rel_path.strip().replace("\\", "/")
        if os.path.isabs(rp) or re.match(r"^[A-Za-z]:", rp):
            raise ValueError(f"Absolute paths not allowed: {rel_path}")
        rp = os.path.normpath(rp).replace("\\", "/")
        if rp.startswith("../") or rp == "..":
            raise ValueError(f"Path escapes workspace: {rel_path}")
        return rp

    def _to_abs(self, rel_path: str) -> str:
        ap = os.path.abspath(os.path.join(self.workspace_root, rel_path))
        if not any(ap == root or ap.startswith(root + os.sep) for root in self.allowed_subpaths):
            raise ValueError(f"Resolved path outside workspace: {ap}")
        return ap

    def parse(self, text: str) -> List[Tuple[str, str]]:
        matches: List[Tuple[int, str, str]] = []
        for m in _FENCED.finditer(text):
            matches.append((m.start(), m.group("path"), m.group("body")))
        if not matches:
            for m in _UNFENCED.finditer(text):
                matches.append((m.start(), m.group("path"), m.group("body")))
        # Sort by position to preserve authoring order
        matches.sort(key=lambda t: t[0])
        return [(p, b.rstrip("\n") + "\n") for _, p, b in matches]

    def plan(self, text: str) -> Plan:
        if not self.detect(text):
            raise ValueError("No '# FILE:' blocks detected.")
        pairs = self.parse(text)
        items: List[WriteItem] = []
        seen = set()
        # Keep last occurrence per path (later overrides earlier)
        for path, body in pairs:
            norm = self._normalize_rel(path)
            abs_path = self._to_abs(norm)
            items.append(WriteItem(rel_path=norm, abs_path=abs_path, content=body.encode("utf-8")))
            seen.add(norm)
        # Deduplicate keeping last occurrences
        dedup: List[WriteItem] = []
        keep = set()
        for it in reversed(items):
            if it.rel_path not in keep:
                keep.add(it.rel_path)
                dedup.append(it)
        dedup.reverse()
        return Plan(self.workspace_root, dedup)

def _cli(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="Extract and write files from '# FILE:' blocks.")
    ap.add_argument("--input","-i",required=True, help="Path to text file containing the blocks")
    ap.add_argument("--workspace","-w",required=True, help="Workspace root (e.g., C:\\AI_Project)")
    ap.add_argument("--apply", action="store_true", help="Write files; default is dry-run")
    ap.add_argument("--json", action="store_true", help="Print JSON summary")
    args = ap.parse_args(argv)

    with open(args.input, "r", encoding="utf-8", errors="ignore") as f:
        txt = f.read()

    ex = MultiFileExtractor(args.workspace)
    if not ex.detect(txt):
        print("No '# FILE:' blocks detected.")
        return 2

    plan = ex.plan(txt)
    out = {"workspace": ex.workspace_root, "count": len(plan.items), "files": [it.rel_path for it in plan.items]}
    if args.json:
        print(json.dumps(out, indent=2))
    else:
        print(Plan.describe.__get__(plan)(plan))
    if args.apply:
        plan.apply()
        print(f"Applied {len(plan.items)} file(s).")
    else:
        print("Dry-run only. Use --apply to write files.")
    return 0

if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
