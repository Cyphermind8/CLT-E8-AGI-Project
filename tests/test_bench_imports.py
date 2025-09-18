# FILE: tests/test_bench_imports.py
def test_bench_scripts_present():
    import os
    assert os.path.exists('bench/tasks_local.jsonl')
    assert os.path.exists('bench/run_bench.py')
