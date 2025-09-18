# scripts/check_cli_contract.py
import os, sys, subprocess

def run(args):
    p = subprocess.run([sys.executable, "self_mod/gated_loop.py", *args],
                       text=True, capture_output=True, env=os.environ.copy())
    return p

def main():
    env_flags = ["--cycle","1","--path", os.environ.get("TARGET_FILE","code_analysis.py")]
    # 1) Accept --strict
    p1 = run(env_flags + ["--strict"])
    # 2) Accept unknown flags
    p2 = run(env_flags + ["--strict","--totally-unknown","xyz"])

    def bad(p): return p.returncode == 2 or "unrecognized arguments" in (p.stderr or "").lower()
    if bad(p1) or bad(p2):
        sys.stderr.write("[!] CLI contract failed. STDERR:\n" + (p1.stderr or "") + (p2.stderr or ""))
        sys.exit(2)
    print("[✓] CLI contract OK.")
    sys.exit(0)

if __name__ == "__main__":
    main()
