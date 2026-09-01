"""gradlew-mcp: MCP server wrapping Gradle for AI agents."""

from importlib.metadata import PackageNotFoundError, version as _v

try:
    __version__ = _v("gradlew-mcp")
except PackageNotFoundError:
    __version__ = "0.1.0"
