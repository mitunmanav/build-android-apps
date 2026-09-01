"""play-store-mcp: Google Play Developer API client (upload + manage listings)."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

log = logging.getLogger("play_store_mcp")

mcp = MCPServer(
    name="play-store-mcp",
    version="0.1.0",
    instructions=(
        "Tools for the Google Play Developer API. Requires a service account "
        "JSON key at .build-android/service-account.json. The first call to "
        "`auth` exchanges the key for an OAuth token and caches it."
    ),
)

CACHE_DIR = Path(os.environ.get("PLAY_STORE_CACHE", ".build-android/play-cache"))
TOKEN_FILE = CACHE_DIR / "token.json"


def _load_token() -> dict | None:
    if TOKEN_FILE.exists():
        try:
            return json.loads(TOKEN_FILE.read_text())
        except json.JSONDecodeError:
            return None
    return None


def _save_token(token: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(json.dumps(token, indent=2))


def _run_curl(args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(args, capture_output=True, text=True, timeout=300)
    return proc.returncode, proc.stdout, proc.stderr


@mcp.tool(
    name="auth",
    title="Authenticate via service account",
    description=(
        "Authenticate to the Google Play Developer API using a service account "
        "JSON key. Caches the OAuth token at .build-android/play-cache/token.json."
    ),
    annotations=ToolAnnotations(
        title="Auth", read_only_hint=False, destructive_hint=False,
        idempotent_hint=True, open_world_hint=True,
    ),
)
def shutil_which_path(name: str) -> str | None:
    import shutil
    return shutil.which(name)


async def auth(service_account_json: str = ".build-android/service-account.json") -> dict[str, Any]:
    sa = Path(service_account_json)
    if not sa.exists():
        return {"ok": False, "error": f"service account JSON not found at {sa}"}
    # Use gcloud if available; otherwise instruct the user
    gcloud_path = shutil_which_path("gcloud")
    if not gcloud_path:
        return {"ok": False, "error": "gcloud CLI not on PATH. Install from https://cloud.google.com/sdk"}
    cmd = ["gcloud", "auth", "activate-service-account", "--key-file", str(sa)]
    code, out, err = _run_curl(cmd)
    if code != 0:
        return {"ok": False, "error": "gcloud auth failed", "stderr": err[-300:]}
    cmd = ["gcloud", "auth", "print-access-token", "--scopes=https://www.googleapis.com/auth/androidpublisher"]
    code, out, err = _run_curl(cmd)
    if code != 0:
        return {"ok": False, "error": "token fetch failed", "stderr": err[-300:]}
    token = out.strip()
    _save_token({"access_token": token, "scopes": "androidpublisher"})
    return {"ok": True, "expires_in": 3600}




@mcp.tool(
    name="upload_aab",
    title="Upload AAB to internal test track",
    description=(
        "Upload a signed release AAB to the internal test track of the "
        "configured app. Requires auth to have been called first."
    ),
    annotations=ToolAnnotations(
        title="Upload AAB", read_only_hint=False, destructive_hint=True,
        idempotent_hint=False, open_world_hint=True,
    ),
)
async def upload_aab(
    package_name: str,
    aab_path: str,
    track: str = "internal",
    service_account_json: str = ".build-android/service-account.json",
) -> dict[str, Any]:
    aab = Path(aab_path)
    if not aab.exists():
        return {"ok": False, "error": f"AAB not found at {aab}"}
    token = _load_token()
    if not token:
        return {"ok": False, "error": "not authenticated; call auth first"}
    edit_url = (
        f"https://androidpublisher.googleapis.com/androidpublisher/v3/applications/{package_name}/edits"
    )
    cmd = [
        "curl", "-sS",
        "-H", f"Authorization: Bearer {token['access_token']}",
        "-H", "Content-Type: application/json",
        "-d", '{"id": "upload-edit"}',
        edit_url,
    ]
    code, out, err = _run_curl(cmd)
    if code != 0 or not out.startswith("{"):
        return {"ok": False, "error": "could not create edit", "stderr": err[-300:]}
    edit = json.loads(out)
    upload_url = (
        f"https://androidpublisher.googleapis.com/upload/androidpublisher/v3/applications/{package_name}"
        f"/edits/{edit['id']}/bundles?uploadType=media"
    )
    cmd2 = [
        "curl", "-sS",
        "-H", f"Authorization: Bearer {token['access_token']}",
        "-H", "Content-Type: application/octet-stream",
        "--data-binary", f"@{aab}",
        upload_url,
    ]
    code2, out2, err2 = _run_curl(cmd2)
    if code2 != 0:
        return {"ok": False, "error": "upload failed", "stderr": err2[-300:]}
    bundle = json.loads(out2)
    track_url = (
        f"https://androidpublisher.googleapis.com/androidpublisher/v3/applications/{package_name}"
        f"/edits/{edit['id']}/tracks/{track}"
    )
    body = {"track": track, "releases": [{"name": bundle["versionCode"], "status": "completed", "versionCodes": [str(bundle["versionCode"])]}]}
    cmd3 = [
        "curl", "-sS", "-X", "PUT",
        "-H", f"Authorization: Bearer {token['access_token']}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(body),
        track_url,
    ]
    code3, out3, err3 = _run_curl(cmd3)
    if code3 != 0:
        return {"ok": False, "error": "track assign failed", "stderr": err3[-300:]}
    commit_url = f"{edit_url}:commit"
    cmd4 = [
        "curl", "-sS", "-X", "POST",
        "-H", f"Authorization: Bearer {token['access_token']}",
        commit_url,
    ]
    code4, out4, err4 = _run_curl(cmd4)
    if code4 != 0:
        return {"ok": False, "error": "commit failed", "stderr": err4[-300:]}
    return {"ok": True, "track": track, "version_code": bundle["versionCode"], "edit_committed": True}


@mcp.tool(
    name="upload_listing",
    title="Upload localized store listing",
    description=(
        "Upload a localized store listing (title, short desc, full desc) to "
        "a Google Play edit. Pass listing as {title, shortDescription, fullDescription, language}."
    ),
    annotations=ToolAnnotations(
        title="Upload Listing", read_only_hint=False, destructive_hint=True,
        idempotent_hint=False, open_world_hint=True,
    ),
)
async def upload_listing(
    package_name: str,
    listing: dict[str, str],
    edit_id: str = "upload-edit",
    language: str = "en-US",
    service_account_json: str = ".build-android/service-account.json",
) -> dict[str, Any]:
    token = _load_token()
    if not token:
        return {"ok": False, "error": "not authenticated; call auth first"}
    url = (
        f"https://androidpublisher.googleapis.com/androidpublisher/v3/applications/{package_name}"
        f"/edits/{edit_id}/listings/{language}"
    )
    cmd = [
        "curl", "-sS", "-X", "PUT",
        "-H", f"Authorization: Bearer {token['access_token']}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(listing),
        url,
    ]
    code, out, err = _run_curl(cmd)
    if code != 0:
        return {"ok": False, "error": "upload listing failed", "stderr": err[-300:]}
    return {"ok": True, "language": language, "uploaded": True}


@mcp.tool(
    name="get_review_status",
    title="Get review status",
    description=(
        "Query the current review status of the app's internal test track. "
        "Returns whether the latest AAB has been approved, rejected, or pending."
    ),
    annotations=ToolAnnotations(
        title="Review Status", read_only_hint=True, destructive_hint=False,
        idempotent_hint=True, open_world_hint=True,
    ),
)
async def get_review_status(
    package_name: str,
    edit_id: str = "upload-edit",
    track: str = "internal",
    service_account_json: str = ".build-android/service-account.json",
) -> dict[str, Any]:
    token = _load_token()
    if not token:
        return {"ok": False, "error": "not authenticated; call auth first"}
    url = (
        f"https://androidpublisher.googleapis.com/androidpublisher/v3/applications/{package_name}"
        f"/edits/{edit_id}/tracks/{track}"
    )
    cmd = [
        "curl", "-sS",
        "-H", f"Authorization: Bearer {token['access_token']}",
        url,
    ]
    code, out, err = _run_curl(cmd)
    if code != 0:
        return {"ok": False, "error": "fetch failed", "stderr": err[-300:]}
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return {"ok": False, "error": "non-JSON response", "body": out[:200]}
    return {"ok": True, "track": track, "data": data}


@mcp.tool(
    name="list_rejections",
    title="List past rejections",
    description=(
        "List past rejections for the app. Each entry has id, reason, "
        "and a suggested fix the rejection-parser subagent can act on."
    ),
    annotations=ToolAnnotations(
        title="List Rejections", read_only_hint=True, destructive_hint=False,
        idempotent_hint=True, open_world_hint=True,
    ),
)
async def list_rejections(
    package_name: str,
    service_account_json: str = ".build-android/service-account.json",
) -> dict[str, Any]:
    token = _load_token()
    if not token:
        return {"ok": False, "error": "not authenticated; call auth first"}
    # Play Console doesn't have a public "list rejections" endpoint; this is a stub that
    # reads from state.json's `rejections` array instead. The actual rejection stream
    # comes via email + Play Console web UI.
    state_path = Path(".build-android/state.json")
    if not state_path.exists():
        return {"ok": True, "rejections": []}
    state = json.loads(state_path.read_text())
    return {"ok": True, "rejections": state.get("rejections", [])}


@mcp.tool(
    name="submit_for_review",
    title="Submit for review",
    description=(
        "Submit the current edit for Google Play review. Only valid if the "
        "track's releases are in 'completed' status."
    ),
    annotations=ToolAnnotations(
        title="Submit", read_only_hint=False, destructive_hint=True,
        idempotent_hint=False, open_world_hint=True,
    ),
)
async def submit_for_review(
    package_name: str,
    edit_id: str = "upload-edit",
    service_account_json: str = ".build-android/service-account.json",
) -> dict[str, Any]:
    token = _load_token()
    if not token:
        return {"ok": False, "error": "not authenticated; call auth first"}
    url = (
        f"https://androidpublisher.googleapis.com/androidpublisher/v3/applications/{package_name}"
        f"/edits/{edit_id}:commit"
    )
    cmd = [
        "curl", "-sS", "-X", "POST",
        "-H", f"Authorization: Bearer {token['access_token']}",
        url,
    ]
    code, out, err = _run_curl(cmd)
    if code != 0:
        return {"ok": False, "error": "submit failed", "stderr": err[-300:]}
    return {"ok": True, "submitted": True}


@mcp.tool(
    name="rollout_staged",
    title="Staged rollout",
    description=(
        "Roll out the latest release to a percentage of production users. "
        "Supports 1, 10, 50, 100 (Play Store does not allow arbitrary percents)."
    ),
    annotations=ToolAnnotations(
        title="Staged Rollout", read_only_hint=False, destructive_hint=True,
        idempotent_hint=False, open_world_hint=True,
    ),
)
async def rollout_staged(
    package_name: str,
    percent: int,
    edit_id: str = "upload-edit",
    service_account_json: str = ".build-android/service-account.json",
) -> dict[str, Any]:
    if percent not in (1, 10, 50, 100):
        return {"ok": False, "error": "percent must be one of 1, 10, 50, 100"}
    token = _load_token()
    if not token:
        return {"ok": False, "error": "not authenticated; call auth first"}
    url = (
        f"https://androidpublisher.googleapis.com/androidpublisher/v3/applications/{package_name}"
        f"/edits/{edit_id}/tracks/production"
    )
    body = {"track": "production", "releases": [{"userFraction": percent / 100, "status": "inProgress"}]}
    cmd = [
        "curl", "-sS", "-X", "PUT",
        "-H", f"Authorization: Bearer {token['access_token']}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(body),
        url,
    ]
    code, out, err = _run_curl(cmd)
    if code != 0:
        return {"ok": False, "error": "rollout failed", "stderr": err[-300:]}
    return {"ok": True, "percent": percent}


@mcp.tool(
    name="get_stats",
    title="Get store stats",
    description=(
        "Fetch basic store stats: download count, average rating, review count, "
        "crash count from Crashlytics. Requires Firebase + Play Console permissions."
    ),
    annotations=ToolAnnotations(
        title="Stats", read_only_hint=True, destructive_hint=False,
        idempotent_hint=True, open_world_hint=True,
    ),
)
async def get_stats(
    package_name: str,
    service_account_json: str = ".build-android/service-account.json",
) -> dict[str, Any]:
    token = _load_token()
    if not token:
        return {"ok": False, "error": "not authenticated; call auth first"}
    # Stub: real impl would query Firebase + Play Reporting APIs.
    return {
        "ok": True,
        "package_name": package_name,
        "note": "Stats require Firebase + Play Reporting scopes; stubbed in v1.0.0",
    }


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        stream=sys.stderr,
    )
    try:
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        log.info("play-store-mcp stopped")


if __name__ == "__main__":
    main()
