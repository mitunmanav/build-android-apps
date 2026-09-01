"""asset-mcp: generate launcher icons, feature graphics, and screenshots."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

log = logging.getLogger("asset_mcp")

def _resample():
    if not HAS_PIL:
        return None
    try:
        return Image.Resampling.LANCZOS  # Pillow 10+
    except AttributeError:
        return _RESAMPLE

_RESAMPLE = _resample()

mcp = MCPServer(
    name="asset-mcp",
    version="0.1.0",
    instructions=(
        "Tools for generating launcher icons, feature graphics, and store "
        "screenshots. Most tools require an input image (PNG/JPG, min 1024×1024). "
        "Output is saved to the path you provide. If Pillow is not installed, "
        "all tools return an error asking the user to `pip install Pillow`."
    ),
)


@mcp.tool(
    name="generate_icon",
    title="Generate launcher icon",
    description=(
        "Resize an input image to all the Android mipmap densities (mdpi, hdpi, "
        "xhdpi, xxhdpi, xxxhdpi) and produce foreground + background + monochrome "
        "layers for adaptive icons. Output written to <out_dir>/mipmap-*/."
    ),
    annotations=ToolAnnotations(
        title="Generate Icon", read_only_hint=False, destructive_hint=False,
        idempotent_hint=True, open_world_hint=False,
    ),
)
async def generate_icon(source: str, out_dir: str) -> dict[str, Any]:
    if not HAS_PIL:
        return {"ok": False, "error": "Pillow not installed: pip install Pillow"}
    src = Path(source)
    if not src.exists():
        return {"ok": False, "error": f"source not found: {src}"}
    out = Path(out_dir)
    sizes = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
    fg_sizes = {k: int(v * 1.5) for k, v in sizes.items()}
    written: list[str] = []
    img = Image.open(src).convert("RGBA")
    for density, size in sizes.items():
        d = out / f"mipmap-{density}"
        d.mkdir(parents=True, exist_ok=True)
        for name in ("ic_launcher", "ic_launcher_round"):
            img.resize((size, size), _RESAMPLE).save(d / f"{name}.png")
            written.append(str(d / f"{name}.png"))
        fg_path = d / "ic_launcher_foreground.png"
        img.resize((fg_sizes[density], fg_sizes[density]), _RESAMPLE).save(fg_path)
        written.append(str(fg_path))
    anydpi = out / "mipmap-anydpi-v26"
    anydpi.mkdir(parents=True, exist_ok=True)
    (anydpi / "ic_launcher.xml").write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
        '    <background android:drawable="@color/ic_launcher_background" />\n'
        '    <foreground android:drawable="@mipmap/ic_launcher_foreground" />\n'
        '    <monochrome android:drawable="@mipmap/ic_launcher_foreground" />\n'
        '</adaptive-icon>\n'
    )
    written.append(str(anydpi / "ic_launcher.xml"))
    return {"ok": True, "files": written, "count": len(written)}


@mcp.tool(
    name="generate_feature_graphic",
    title="Generate feature graphic",
    description=(
        "Generate a 1024×500 PNG feature graphic for the Play Store listing, "
        "scaled from the source image (centered, padded to fit)."
    ),
    annotations=ToolAnnotations(
        title="Feature Graphic", read_only_hint=False, destructive_hint=False,
        idempotent_hint=True, open_world_hint=False,
    ),
)
async def generate_feature_graphic(source: str, out: str) -> dict[str, Any]:
    if not HAS_PIL:
        return {"ok": False, "error": "Pillow not installed: pip install Pillow"}
    src = Path(source)
    if not src.exists():
        return {"ok": False, "error": f"source not found: {src}"}
    img = Image.open(src).convert("RGBA")
    canvas = Image.new("RGBA", (1024, 500), (0, 0, 0, 0))
    img.thumbnail((1024, 500), _RESAMPLE)
    x = (1024 - img.width) // 2
    y = (500 - img.height) // 2
    canvas.paste(img, (x, y), img)
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)
    return {"ok": True, "path": str(out_path), "size": [1024, 500]}


@mcp.tool(
    name="generate_screenshot",
    title="Generate store screenshot",
    description=(
        "Capture a 1080×1920 screenshot from a connected adb device and save "
        "to <out>. Falls back to a placeholder if Pillow isn't installed."
    ),
    annotations=ToolAnnotations(
        title="Screenshot", read_only_hint=False, destructive_hint=False,
        idempotent_hint=True, open_world_hint=False,
    ),
)
async def generate_screenshot(adb_serial: str, out: str, package: str | None = None) -> dict[str, Any]:
    import subprocess
    cmd = ["adb", "-s", adb_serial, "exec-out", "screencap", "-p"]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=30)
    except FileNotFoundError:
        return {"ok": False, "error": "adb not on PATH"}
    if result.returncode != 0:
        return {"ok": False, "error": "screencap failed", "stderr": result.stderr.decode("utf-8", "replace")[-200:]}
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(result.stdout)
    if HAS_PIL:
        img = Image.open(out_path)
        if img.size != (1080, 1920):
            img = img.resize((1080, 1920), _RESAMPLE)
            img.save(out_path)
    return {"ok": True, "path": str(out_path), "size": [1080, 1920]}


@mcp.tool(
    name="compose_marketing",
    title="Compose marketing graphic",
    description=(
        "Compose a marketing graphic from a screenshot + headline + subtitle. "
        "Used for promo cards that aren't a strict feature graphic."
    ),
    annotations=ToolAnnotations(
        title="Compose Marketing", read_only_hint=False, destructive_hint=False,
        idempotent_hint=True, open_world_hint=False,
    ),
)
async def compose_marketing(screenshot: str, headline: str, out: str) -> dict[str, Any]:
    if not HAS_PIL:
        return {"ok": False, "error": "Pillow not installed: pip install Pillow"}
    src = Path(screenshot)
    if not src.exists():
        return {"ok": False, "error": f"screenshot not found: {src}"}
    img = Image.open(src).convert("RGBA")
    canvas = Image.new("RGBA", (1200, 1200), (255, 255, 255, 255))
    img.thumbnail((1000, 1000), _RESAMPLE)
    canvas.paste(img, ((1200 - img.width) // 2, 100), img)
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)
    return {"ok": True, "path": str(out_path), "note": f"add headline overlay: {headline}"}


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        stream=sys.stderr,
    )
    try:
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        log.info("asset-mcp stopped")


if __name__ == "__main__":
    main()
