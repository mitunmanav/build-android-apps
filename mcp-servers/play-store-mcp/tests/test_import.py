import importlib
def test_import():
    mod = importlib.import_module("play_store_mcp")
    assert mod is not None

def test_dummy():
    assert True
