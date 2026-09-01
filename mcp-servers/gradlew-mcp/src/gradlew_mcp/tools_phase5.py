"""Extra gradlew-mcp tools for Phase 5 (scaffold + keystore + introspection).

Adds:
    describe_project   — introspect Gradle build targets + APK paths
    manage_sdk         — wrap `sdkmanager` for SDK install/upgrade
    run_help           — lightweight verification gate (`./gradlew help`)
    run_build_dry      — lightweight verification gate (`./gradlew build --dry-run`)
    generate_keystore  — create upload keystore (elicitation for password)
    verify_keystore    — validate keystore + alias + passwords match
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from mcp.types import ToolAnnotations

from . import runner


def register(server) -> None:
    @server.tool(
        name="describe_project",
        title="Describe Android project",
        description=(
            "Read the Gradle build files and return a JSON description of the "
            "project: modules, application id, versions (min/target/compile), "
            "expected APK and AAB output paths. Use this to verify a project "
            "was scaffolded correctly without running a full build."
        ),
        annotations=ToolAnnotations(
            title="Describe Project", read_only_hint=True, destructive_hint=False,
            idempotent_hint=True, open_world_hint=False,
        ),
    )
    async def describe_project(cwd: str | None = None) -> dict[str, Any]:
        root = Path(cwd or ".")
        info: dict[str, Any] = {"root": str(root.resolve()), "modules": [], "warnings": []}
        settings = root / "settings.gradle.kts"
        if not settings.exists():
            settings = root / "settings.gradle"
        if settings.exists():
            for m in re.findall(r"include\(\s*[\"']([^\"']+)[\"']\s*\)", settings.read_text()):
                info["modules"].append(m)
        app_gradle = root / "app" / "build.gradle.kts"
        if not app_gradle.exists():
            app_gradle = root / "app" / "build.gradle"
        if app_gradle.exists():
            text = app_gradle.read_text()
            ns = re.search(r"namespace\s*=\s*\"([^\"]+)\"", text)
            if ns:
                info["application_id"] = ns.group(1)
            mn = re.search(r"minSdk\s*=\s*(\d+)", text)
            tg = re.search(r"targetSdk\s*=\s*(\d+)", text)
            agp = re.search(r"com\.android\.application", text)
            if mn:
                info["min_sdk"] = int(mn.group(1))
            if tg:
                info["target_sdk"] = int(tg.group(1))
            info["is_android_app"] = bool(agp)
        if info.get("application_id"):
            app_id_safe = info["application_id"].replace(".", "/")
            info["apk_path"] = f"app/build/outputs/apk/debug/app-debug.apk"
            info["aab_path"] = f"app/build/outputs/bundle/release/app-release.aab"
        return info

    @server.tool(
        name="manage_sdk",
        title="Manage Android SDK packages",
        description=(
            "Wrapper around `sdkmanager` for installing/upgrading Android SDK "
            "packages. Pass `install` with a list of package ids (e.g. "
            "['platforms;android-34', 'build-tools;34.0.0']) or `list` to enumerate."
        ),
        annotations=ToolAnnotations(
            title="Manage SDK", read_only_hint=False, destructive_hint=True,
            idempotent_hint=False, open_world_hint=True,
        ),
    )
    async def manage_sdk(action: str, packages: list[str] | None = None) -> dict[str, Any]:
        sdk = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
        if not sdk:
            return {"ok": False, "error": "ANDROID_HOME or ANDROID_SDK_ROOT not set"}
        sdkman = Path(sdk) / "cmdline-tools" / "latest" / "bin" / "sdkmanager"
        if not sdkman.exists():
            for p in Path(sdk).rglob("sdkmanager"):
                sdkman = p
                break
        if not sdkman.exists():
            return {"ok": False, "error": f"sdkmanager not found under {sdk}"}
        if action == "list":
            cmd = [str(sdkman), "--list"]
        elif action == "install":
            cmd = [str(sdkman), *(packages or [])]
        else:
            return {"ok": False, "error": f"unknown action: {action}"}
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout_tail": "\n".join(proc.stdout.splitlines()[-30:]),
            "stderr_tail": "\n".join(proc.stderr.splitlines()[-15:]),
        }

    @server.tool(
        name="run_help",
        title="Lightweight verification (./gradlew help)",
        description=(
            "Run `./gradlew help` as a fast check that Gradle is wired correctly. "
            "Does NOT compile any code. Use as a pre-flight sanity check before "
            "a longer assembleDebug run."
        ),
        annotations=ToolAnnotations(
            title="Run help", read_only_hint=True, destructive_hint=False,
            idempotent_hint=True, open_world_hint=False,
        ),
    )
    async def run_help(cwd: str | None = None, timeout: float = 120.0) -> dict[str, Any]:
        result = await runner.run("help", cwd=cwd or ".", timeout=timeout)
        return {
            "ok": result.ok,
            "task": "help",
            "returncode": result.returncode,
            "tail": "\n".join(result.stdout.splitlines()[-15:]),
        }

    @server.tool(
        name="run_build_dry",
        title="Lightweight verification (./gradlew build --dry-run)",
        description=(
            "Run `./gradlew build --dry-run` to verify the project's task graph "
            "without executing any tasks. Useful for catching configuration errors "
            "without waiting for a full build."
        ),
        annotations=ToolAnnotations(
            title="Build dry-run", read_only_hint=True, destructive_hint=False,
            idempotent_hint=True, open_world_hint=False,
        ),
    )
    async def run_build_dry(cwd: str | None = None, timeout: float = 180.0) -> dict[str, Any]:
        result = await runner.run("build", "--dry-run", cwd=cwd or ".", timeout=timeout)
        return {
            "ok": result.ok,
            "task": "build --dry-run",
            "returncode": result.returncode,
            "tail": "\n".join(result.stdout.splitlines()[-25:]),
        }

    @server.tool(
        name="generate_keystore",
        title="Generate upload keystore",
        description=(
            "Generate an upload keystore for Play Store signing. Defaults: "
            "RSA 2048, validity 25 years, alias 'upload'. The keystore is saved "
            "to <cwd>/.build-android/upload-keystore.jks. The keystore password "
            "and key password MUST be supplied via the password + key_password "
            "arguments. WARNING: if you lose the keystore, you cannot update the "
            "app on Play Store. Back it up immediately."
        ),
        annotations=ToolAnnotations(
            title="Generate keystore", read_only_hint=False, destructive_hint=True,
            idempotent_hint=False, open_world_hint=False,
        ),
    )
    async def generate_keystore(
        password: str,
        key_password: str | None = None,
        alias: str = "upload",
        validity_days: int = 9125,
        cwd: str | None = None,
    ) -> dict[str, Any]:
        key_password = key_password or password
        root = Path(cwd or ".")
        out_dir = root / ".build-android"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "upload-keystore.jks"
        if out_path.exists():
            return {"ok": False, "error": f"keystore already exists at {out_path}"}
        keytool = shutil.which("keytool")
        if not keytool:
            return {"ok": False, "error": "keytool not on PATH (install JDK 17+)"}
        cmd = [
            keytool, "-genkeypair",
            "-keystore", str(out_path),
            "-alias", alias,
            "-keyalg", "RSA",
            "-keysize", "2048",
            "-validity", str(validity_days),
            "-storepass", password,
            "-keypass", key_password,
            "-dname", "CN=Android, OU=Mobile, O=App, L=NA, S=NA, C=NA",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if proc.returncode != 0:
            return {"ok": False, "error": "keytool failed", "stderr": proc.stderr[-500:]}
        # Compute SHA-256 fingerprint
        fp_proc = subprocess.run(
            [keytool, "-list", "-v", "-keystore", str(out_path), "-storepass", password],
            capture_output=True, text=True, timeout=30,
        )
        fingerprint = ""
        for line in fp_proc.stdout.splitlines():
            if "SHA-256:" in line or "SHA256:" in line:
                fingerprint = line.split(":", 1)[1].strip()
                break
        return {
            "ok": True,
            "keystore_path": str(out_path),
            "alias": alias,
            "fingerprint": fingerprint,
            "warning": "BACK UP THIS KEYSTORE NOW. If lost, you cannot update the app.",
        }

    @server.tool(
        name="verify_keystore",
        title="Verify upload keystore",
        description=(
            "Validate a keystore: file exists, alias exists, both passwords match, "
            "and return the SHA-256 fingerprint. Use this before /publish to "
            "confirm the signing config is wired correctly."
        ),
        annotations=ToolAnnotations(
            title="Verify keystore", read_only_hint=True, destructive_hint=False,
            idempotent_hint=True, open_world_hint=False,
        ),
    )
    async def verify_keystore(
        keystore_path: str,
        alias: str,
        password: str,
        key_password: str | None = None,
    ) -> dict[str, Any]:
        key_password = key_password or password
        path = Path(keystore_path)
        if not path.exists():
            return {"ok": False, "error": f"keystore not found at {path}"}
        keytool = shutil.which("keytool")
        if not keytool:
            return {"ok": False, "error": "keytool not on PATH"}
        proc = subprocess.run(
            [keytool, "-list", "-v", "-keystore", str(path),
             "-storepass", password, "-alias", alias, "-keypass", key_password],
            capture_output=True, text=True, timeout=30,
        )
        if proc.returncode != 0:
            return {"ok": False, "error": "verification failed", "stderr_tail": proc.stderr[-300:]}
        fingerprint = ""
        for line in proc.stdout.splitlines():
            if "SHA-256:" in line or "SHA256:" in line:
                fingerprint = line.split(":", 1)[1].strip()
                break
        return {"ok": True, "fingerprint": fingerprint, "alias": alias}
