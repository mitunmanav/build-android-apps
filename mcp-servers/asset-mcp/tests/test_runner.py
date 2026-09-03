"""Runner smoke for asset-mcp (baseline overhaul)."""
import pathlib

def test_tool_surface():
    src = __import__('pathlib').Path(__file__).resolve().parent.parent / "asset_mcp" / "server.py"
    text = src.read_text() if src.exists() else ""
    # flat-layout fallback
    if not text:
        import pathlib as _pl
        alt = _pl.Path(__file__).resolve().parent.parent / "asset_mcp" / "server.py"
        text = alt.read_text() if alt.exists() else ""
    for tool in ['generate_icon', 'generate_feature_graphic', 'generate_screenshot', 'compose_marketing']:
        assert tool in text, f"missing tool {tool} in asset-mcp server.py"
