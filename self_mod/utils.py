# FILE: self_mod/utils.py
from __future__ import annotations
import os, json, shutil, tempfile, difflib, hashlib, time, subprocess, sys
from pathlib import Path
from typing import Dict, Any, Tuple

IGNORE_DIRS = {'.venv','runs','reports','__pycache__','.git','.pytest_cache','data'}

def sha12(s: str) -> str:
    import hashlib
    return hashlib.sha256(s.encode('utf-8')).hexdigest()[:12]

def copy_repo_to_temp(root: Path) -> Path:
    tempdir = Path(tempfile.mkdtemp(prefix='clte8_scratch_'))
    for item in root.iterdir():
        name = item.name
        if name in IGNORE_DIRS:
            continue
        dst = tempdir / name
        if item.is_dir():
            shutil.copytree(item, dst)
        else:
            shutil.copy2(item, dst)
    return tempdir

def unified_diff(old_text: str, new_text: str, fromfile: str, tofile: str) -> str:
    diff = difflib.unified_diff(
        old_text.splitlines(keepends=True),
        new_text.splitlines(keepends=True),
        fromfile=fromfile, tofile=tofile, lineterm=''
    )
    return ''.join(diff)

def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(content, encoding='utf-8')
    tmp.replace(path)

def run_pytest(cwd: Path, timeout_s: int = 300) -> Tuple[bool,str]:
    try:
        p = subprocess.run([sys.executable, '-m', 'pytest', '-q'], cwd=str(cwd), capture_output=True, text=True, timeout=timeout_s)
        return (p.returncode == 0, (p.stdout or '') + (p.stderr or ''))
    except subprocess.TimeoutExpired as e:
        return (False, f'Timeout after {timeout_s}s')

def run_bench(cwd: Path, determinism_runs: int = 1, timeout_s: int = 600) -> Tuple[bool, Dict[str,Any], str]:
    try:
        p = subprocess.run([sys.executable, 'bench/run_bench.py', '--determinism', str(determinism_runs), '--outdir', 'reports'],
                           cwd=str(cwd), capture_output=True, text=True, timeout=timeout_s)
        ok = (p.returncode == 0)
        # Attempt to parse printed JSON with output paths
        info = {}
        try:
            info = json.loads(p.stdout).get('outputs', {})
        except Exception:
            pass
        # Find latest bench json in reports
        reports = Path(cwd) / 'reports'
        latest = None
        for f in reports.glob('bench_*.json'):
            if latest is None or f.stat().st_mtime > latest.stat().st_mtime:
                latest = f
        bench_data = {}
        if latest and latest.exists():
            bench_data = json.loads(latest.read_text(encoding='utf-8'))
        return (ok, bench_data, p.stdout + p.stderr)
    except subprocess.TimeoutExpired:
        return (False, {}, f'Timeout after {timeout_s}s')

def score_from_bench(bench: Dict[str,Any]) -> Tuple[float, float, bool]:
    sr = float(bench.get('success', {}).get('rate', 0.0))
    avg_lat = float(bench.get('latency', {}).get('avg_s', 1e9))
    det_ok = bool(bench.get('determinism_ok', False))
    return sr, avg_lat, det_ok
