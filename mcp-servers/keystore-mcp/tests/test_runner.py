"""Runner smoke for keystore-mcp (baseline overhaul)."""
import pathlib

def test_tool_surface():
    src = __import__('pathlib').Path(__file__).resolve().parent.parent / "keystore_mcp" / "server.py"
    text = src.read_text() if src.exists() else ""
    # flat-layout fallback
    if not text:
        import pathlib as _pl
        alt = _pl.Path(__file__).resolve().parent.parent / "keystore_mcp" / "server.py"
        text = alt.read_text() if alt.exists() else ""
    for tool in ['generate', 'verify', 'rotate', 'backup', 'fingerprint']:
        assert tool in text, f"missing tool {tool} in keystore-mcp server.py"
