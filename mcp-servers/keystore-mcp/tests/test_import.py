import importlib
def test_import():
    mod = importlib.import_module("keystore_mcp")
    assert mod is not None

def test_dummy():
    assert True
