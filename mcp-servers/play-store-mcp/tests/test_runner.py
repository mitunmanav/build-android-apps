"""Runner smoke for play-store-mcp (baseline overhaul)."""
import pathlib

def test_tool_surface():
    src = __import__('pathlib').Path(__file__).resolve().parent.parent / "play_store_mcp" / "server.py"
    text = src.read_text() if src.exists() else ""
    # flat-layout fallback
    if not text:
        import pathlib as _pl
        alt = _pl.Path(__file__).resolve().parent.parent / "play_store_mcp" / "server.py"
        text = alt.read_text() if alt.exists() else ""
    for tool in ['auth', 'upload_aab', 'upload_listing', 'get_review_status', 'list_rejections', 'submit_for_review', 'rollout_staged', 'get_stats']:
        assert tool in text, f"missing tool {tool} in play-store-mcp server.py"
