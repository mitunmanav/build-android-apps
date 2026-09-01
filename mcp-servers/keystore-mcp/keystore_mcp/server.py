"""keystore-mcp: dedicated upload keystore operations (canonical home)."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

log = logging.getLogger("keystore_mcp")

mcp = MCPServer(
    name="keystore-mcp",
    version="0.1.0",
    instructions=(
        "Canonical home for upload keystore operations: generate, verify, "
        "rotate, backup, fingerprint. Always warn the user to back up the "
        "keystore before destructive operations."
    ),
)


def _keytool() -> str | None:
    return shutil.which("keytool")


def _fingerprint_of(path: Path, password: str, alias: str, key_password: str | None = None) -> str:
    key_password = key_password or password
    proc = subprocess.run(
        [_keytool(), "-list", "-v", "-keystore", str(path),
         "-storepass", password, "-alias", alias, "-keypass", key_password],
        capture_output=True, text=True, timeout=30,
    )
    for line in proc.stdout.splitlines():
        if "SHA-256:" in line or "SHA256:" in line:
            return line.split(":", 1)[1].strip()
    return ""


@mcp.tool(
    name="generate",
    title="Generate upload keystore",
    description=(
        "Generate an upload keystore for Play Store signing. RSA 2048, "
        "validity 25 years, alias 'upload'. Saved to <out>/upload-keystore.jks. "
        "WARNING: if lost, you cannot update the app on Play Store."
    ),
    annotations=ToolAnnotations(
        title="Generate", read_only_hint=False, destructive_hint=True,
        idempotent_hint=False, open_world_hint=False,
    ),
)
async def generate(
    password: str,
    key_password: str | None = None,
    alias: str = "upload",
    validity_days: int = 9125,
    out: str = ".build-android/upload-keystore.jks",
) -> dict[str, Any]:
    keytool = _keytool()
    if not keytool:
        return {"ok": False, "error": "keytool not on PATH (install JDK 17+)"}
    out_path = Path(out)
    if out_path.exists():
        return {"ok": False, "error": f"keystore already exists at {out_path}"}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        keytool, "-genkeypair",
        "-keystore", str(out_path),
        "-alias", alias,
        "-keyalg", "RSA",
        "-keysize", "2048",
        "-validity", str(validity_days),
        "-storepass", password,
        "-keypass", key_password or password,
        "-dname", "CN=Android, OU=Mobile, O=App, L=NA, S=NA, C=NA",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if proc.returncode != 0:
        return {"ok": False, "error": "keytool failed", "stderr": proc.stderr[-500:]}
    fp = _fingerprint_of(out_path, password, alias, key_password)
    return {
        "ok": True,
        "path": str(out_path),
        "alias": alias,
        "fingerprint": fp,
        "warning": "BACK UP THIS KEYSTORE NOW. If lost, you cannot update the app.",
    }


@mcp.tool(
    name="verify",
    title="Verify upload keystore",
    description=(
        "Validate a keystore: file exists, alias exists, both passwords match, "
        "return the SHA-256 fingerprint. Use this before /publish to confirm "
        "the signing config is wired correctly."
    ),
    annotations=ToolAnnotations(
        title="Verify", read_only_hint=True, destructive_hint=False,
        idempotent_hint=True, open_world_hint=False,
    ),
)
async def verify(
    keystore_path: str,
    alias: str,
    password: str,
    key_password: str | None = None,
) -> dict[str, Any]:
    path = Path(keystore_path)
    if not path.exists():
        return {"ok": False, "error": f"keystore not found at {path}"}
    keytool = _keytool()
    if not keytool:
        return {"ok": False, "error": "keytool not on PATH"}
    proc = subprocess.run(
        [keytool, "-list", "-v", "-keystore", str(path),
         "-storepass", password, "-alias", alias, "-keypass", key_password or password],
        capture_output=True, text=True, timeout=30,
    )
    if proc.returncode != 0:
        return {"ok": False, "error": "verification failed", "stderr_tail": proc.stderr[-300:]}
    return {"ok": True, "fingerprint": _fingerprint_of(path, password, alias, key_password), "alias": alias}


@mcp.tool(
    name="rotate",
    title="Rotate upload keystore",
    description=(
        "Generate a new keystore with the same alias. WARNING: Google Play "
        "lets you upload a new upload key by sending a request, but you cannot "
        "self-serve the rotation. This tool is mostly for testing — for "
        "production, contact Google support."
    ),
    annotations=ToolAnnotations(
        title="Rotate", read_only_hint=False, destructive_hint=True,
        idempotent_hint=False, open_world_hint=False,
    ),
)
async def rotate(
    password: str,
    alias: str = "upload",
    new_path: str = ".build-android/upload-keystore-new.jks",
) -> dict[str, Any]:
    return await generate(password=password, alias=alias, out=new_path)


@mcp.tool(
    name="backup",
    title="Backup keystore",
    description=(
        "Copy the keystore to a target location (e.g., a mounted USB drive or "
        "a Google Drive folder). Always warn the user before running."
    ),
    annotations=ToolAnnotations(
        title="Backup", read_only_hint=False, destructive_hint=True,
        idempotent_hint=True, open_world_hint=False,
    ),
)
async def backup(source: str, destination: str) -> dict[str, Any]:
    src = Path(source)
    dst = Path(destination)
    if not src.exists():
        return {"ok": False, "error": f"source not found: {src}"}
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return {"ok": True, "source": str(src), "destination": str(dst), "size": src.stat().st_size}


@mcp.tool(
    name="fingerprint",
    title="Print SHA-256 fingerprint",
    description=(
        "Return the SHA-256 fingerprint of the keystore for verification "
        "(e.g., to confirm the SHA matches what Play Console shows)."
    ),
    annotations=ToolAnnotations(
        title="Fingerprint", read_only_hint=True, destructive_hint=False,
        idempotent_hint=True, open_world_hint=False,
    ),
)
async def fingerprint(
    keystore_path: str,
    alias: str,
    password: str,
    key_password: str | None = None,
) -> dict[str, Any]:
    path = Path(keystore_path)
    if not path.exists():
        return {"ok": False, "error": f"keystore not found at {path}"}
    fp = _fingerprint_of(path, password, alias, key_password)
    if not fp:
        return {"ok": False, "error": "could not parse fingerprint (wrong alias/password?)"}
    return {"ok": True, "fingerprint": fp}


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        stream=sys.stderr,
    )
    try:
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        log.info("keystore-mcp stopped")


if __name__ == "__main__":
    main()
