import sys, os, subprocess
sys.path.insert(0, r"C:\AI_Project")
from src.utils.runlog import runlog

if __name__ == "__main__":
    with runlog({"runner": "bench/run_bench.py"}):
        subprocess.run([sys.executable, os.path.join("bench","run_bench.py")], check=True)
