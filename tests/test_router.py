"""Router longest-match + ghost-free routing (baseline overhaul)."""
from pathlib import Path

ROUTER = Path(__file__).resolve().parent.parent / "skills" / "build-android-apps" / "references" / "routing-table.md"

def _text():
    return ROUTER.read_text()

def test_router_has_29_plus_rows():
    t = _text()
    # rows 1-50 must exist (28 original + 22 new)
    for n in ["| 29 |", "| 30 |", "| 33 |", "| 35 |", "| 50 |"]:
        assert n in t, f"missing router row {n}"

def test_magic_link_routes_to_verified_email_only():
    t = _text()
    assert "`verify email`, `passwordless`, `magic link`" in t
    # restore row must not claim magic link
    restore_line = [l for l in t.splitlines() if "android-restore-credentials" in l][0]
    assert "magic link" not in restore_line.lower()

def test_run_vs_drive_boundary_documented():
    t = _text().lower()
    assert "run` = install/launch/screenshot" in t or "run`=" in t or "install/launch/screenshot" in t
    assert "tap/swipe/hierarchy" in t

def test_no_ghost_skills_in_router():
    t = _text()
    assert "android-build" not in t or "no specialist skill" in t
    assert "android-play" not in t
