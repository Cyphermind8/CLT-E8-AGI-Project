import sys, os, subprocess
ROOT = r"C:\AI_Project"
sys.path.insert(0, ROOT)

from src.utils.runlog import runlog

if __name__ == "__main__":
    with runlog({"runner": "bench/run_bench.py"}):
        subprocess.run([sys.executable, "-m", "bench.run_bench"], check=True, cwd=ROOT)
