import sys
from scripts.auto_clt_loop import auto_loop

hours = float(sys.argv[1]) if len(sys.argv) > 1 else 10.0
pause = int(sys.argv[2]) if len(sys.argv) > 2 else 300
max_edits = int(sys.argv[3]) if len(sys.argv) > 3 else 50

auto_loop(hours=hours, pause_sec=pause, max_edits=max_edits)
