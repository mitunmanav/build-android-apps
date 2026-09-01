"""adb-mcp: MCP server wrapping the Android Debug Bridge."""

from importlib.metadata import PackageNotFoundError, version as _v

try:
    __version__ = _v("adb-mcp")
except PackageNotFoundError:
    __version__ = "0.1.0"
