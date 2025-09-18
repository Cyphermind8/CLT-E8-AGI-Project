def test_imports_smoke():
    import importlib, sys
    sys.path.insert(0, r"C:\AI_Project")
    assert importlib.import_module("src.auto.llm_client")
    assert importlib.import_module("src.auto.self_improver")
    assert importlib.import_module("src.clt_e8.policy")
