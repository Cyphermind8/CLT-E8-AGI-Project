from __future__ import annotations
import os, io, json
from dataclasses import dataclass
from typing import Optional

DEFAULT_WRITE_ALLOW = [
    "data","backup","reports","experiments","runs","logs","quarantine","temp",
]

@dataclass(frozen=True)
class GovernorConfig:
    project_root: str
    write_allow: tuple[str, ...] = tuple(DEFAULT_WRITE_ALLOW)
    dry_run: bool = False

    @staticmethod
    def from_env(project_root: Optional[str] = None) -> "GovernorConfig":
        root = project_root or os.path.abspath(os.getenv("CLT_E8_PROJECT_ROOT", os.getcwd()))
        allow = os.getenv("CLT_E8_WRITE_ALLOW", ",".join(DEFAULT_WRITE_ALLOW)).split(",")
        allow = tuple(x.strip() for x in allow if x.strip())
        dry = os.getenv("CLT_E8_DRY_RUN", "0").strip() in ("1","true","True")
        return GovernorConfig(project_root=root, write_allow=allow, dry_run=dry)

class Governor:
    def __init__(self, cfg: Optional[GovernorConfig] = None) -> None:
        self.cfg = cfg or GovernorConfig.from_env()

    def _norm(self, path: str) -> str:
        return os.path.abspath(path)

    def _is_under(self, path: str, folder: str) -> bool:
        path, folder = self._norm(path), self._norm(folder)
        try:
            common = os.path.commonpath([path, folder])
        except ValueError:
            return False
        return common == folder

    def is_write_allowed(self, path: str) -> bool:
        apath = self._norm(path)
        root  = self._norm(self.cfg.project_root)
        if not self._is_under(apath, root):
            return False
        for sub in self.cfg.write_allow:
            target = self._norm(os.path.join(root, sub))
            if self._is_under(apath, target):
                return True
        return False

    def ensure_parent(self, path: str) -> None:
        parent = os.path.dirname(self._norm(path))
        if parent and not os.path.isdir(parent):
            if self.cfg.dry_run: return
            os.makedirs(parent, exist_ok=True)

    def write_text(self, path: str, text: str, encoding: str = "utf-8", bom: bool = False) -> None:
        if not self.is_write_allowed(path):
            raise PermissionError(f"Governor blocked write outside allowlist: {path}")
        if self.cfg.dry_run: return
        self.ensure_parent(path)
        if bom:
            with open(path, "wb") as f:
                f.write(b"\xEF\xBB\xBF" + text.encode("utf-8"))
            return
        with io.open(path, "w", encoding=encoding, newline="\n") as f:
            f.write(text)

    def write_json(self, path: str, obj, sort_keys: bool = True, indent: int = 2) -> None:
        payload = json.dumps(obj, ensure_ascii=False, sort_keys=sort_keys, indent=indent)
        self.write_text(path, payload, encoding="utf-8", bom=False)

    def append_text(self, path: str, text: str, encoding: str = "utf-8") -> None:
        if not self.is_write_allowed(path):
            raise PermissionError(f"Governor blocked append outside allowlist: {path}")
        if self.cfg.dry_run: return
        self.ensure_parent(path)
        with io.open(path, "a", encoding=encoding, newline="\n") as f:
            f.write(text)

    def copy_file(self, src: str, dst: str) -> None:
        if not os.path.isfile(src): raise FileNotFoundError(src)
        if not self.is_write_allowed(dst):
            raise PermissionError(f"Governor blocked copy outside allowlist: {dst}")
        if self.cfg.dry_run: return
        self.ensure_parent(dst)
        with open(src, "rb") as r, open(dst, "wb") as w:
            w.write(r.read())

    def approved_targets(self) -> list[str]:
        root = self._norm(self.cfg.project_root)
        return [os.path.join(root, sub) for sub in self.cfg.write_allow]