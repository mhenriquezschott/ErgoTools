"""Repeatable Linux launcher for the isolated Android feasibility application.

Only dedicated cache/staging/AVD paths are managed. Shared source files are copied
byte-for-byte for packaging; desktop environments, dependencies and project files
are never edited. APK replacements retain Android's private app data.
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

# All defaults are owner-specific caches, derived from the current account.
ROOT = Path(__file__).resolve().parents[2]
PROTOTYPE = ROOT / "prototypes/android_demo"
CACHE = Path.home() / ".cache/ergotools-android-demo"
SDK = CACHE / "sdk"
STAGE = CACHE / "app"
FLET = ROOT / "tmp/android-demo-toolchain/venv/bin/flet"
EMULATOR = CACHE / "emulators/36.4.10/emulator/emulator"
AVD = "ErgoTools_Tablet_API35"
SERIAL = "emulator-5580"
PACKAGE = "org.ergotools.tabletdemo"
APK = STAGE / "build/apk/ergotools-android-demo.apk"


def command(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run an argument list without shell interpolation or secret environment output.

    Args:
        args: Exact executable and arguments.
        check: Raise on a nonzero process exit when True.

    Returns:
        Captured command text and exit status.
    """
    return subprocess.run(args, text=True, capture_output=True, check=check)


def adb(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Address only the dedicated prototype emulator, never an attached real device.

    Args:
        args: ADB operation following the fixed serial selection.
        check: Require a successful device operation.

    Returns:
        Captured ADB output.
    """
    return command([str(SDK / "platform-tools/adb"), "-s", SERIAL, *args], check=check)


def source_files() -> list[tuple[Path, Path]]:
    """Map current prototype and unchanged shared Python files into build staging.

    Args:
        None.

    Returns:
        Source/destination-relative pairs, excluding bytecode and desktop adapters.
    """
    files = [(PROTOTYPE / "pyproject.toml", Path("pyproject.toml"))]
    files.extend(
        (p, Path("src") / p.relative_to(PROTOTYPE / "src"))
        for p in sorted((PROTOTYPE / "src").rglob("*"))
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
    )
    package = ROOT / "src/ergotools"
    files.append((package / "__init__.py", Path("src/ergotools/__init__.py")))
    for layer in ("domain", "application", "infrastructure"):
        files.extend(
            (p, Path("src/ergotools") / p.relative_to(package))
            for p in sorted((package / layer).rglob("*.py"))
        )
    return files


def stage_sources() -> str:
    """Refresh owned source staging while preserving Flutter's incremental build cache.

    Args:
        None.

    Returns:
        Deterministic digest of all packaged sources, assets and dependency pins.
    """
    files = source_files()
    digest = hashlib.sha256()
    for original, relative in files:
        digest.update(relative.as_posix().encode())
        digest.update(original.read_bytes())
    STAGE.mkdir(parents=True, exist_ok=True)
    source_root = STAGE / "src"
    if source_root.exists():
        shutil.rmtree(source_root)
    manifest = {}
    for original, relative in files:
        target = STAGE / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original, target)
        manifest[relative.as_posix()] = hashlib.sha256(target.read_bytes()).hexdigest()
    (CACHE / "source_manifest.json").write_text(json.dumps(manifest, indent=2))
    return digest.hexdigest()


def build(force: bool) -> None:
    """Compile changed sources only; a failed build never launches an older APK as new.

    Args:
        force: Explicit --rebuild request.

    Returns:
        None after a verified cached or newly compiled APK is available.

    Raises:
        RuntimeError: The isolated build exits unsuccessfully or produces no APK.
    """
    digest = stage_sources()
    stamp = CACHE / "built_source.sha256"
    if not force and APK.exists() and stamp.exists() and stamp.read_text() == digest:
        print("APK is current; using the existing build.", flush=True)
        return
    print("Building updated tablet app. First builds take longer.", flush=True)
    env = dict(os.environ)
    env["ANDROID_HOME"] = str(SDK)
    env["PATH"] = str(Path.home() / "flutter/3.47.9/bin") + os.pathsep + env["PATH"]
    log = CACHE / "build.log"
    with log.open("w") as output:
        result = subprocess.run(
            [
                str(FLET),
                "build",
                "apk",
                str(STAGE),
                "--arch",
                "x86_64",
                "--python-version",
                "3.13",
                "--yes",
                "--skip-flutter-doctor",
                "--log-format",
                "plain",
            ],
            env=env,
            stdout=output,
            stderr=subprocess.STDOUT,
        )
    if result.returncode or not APK.exists():
        raise RuntimeError(
            f"Android build failed. Details: {log}\n{log.read_text()[-2500:]}"
        )
    stamp.write_text(digest)
    print(f"APK built. Build log: {log}", flush=True)


def boot() -> None:
    """Start or reuse this tablet, waiting for Android readiness before installing.

    Args:
        None.

    Returns:
        None once the dedicated Android instance reports a completed boot.

    Raises:
        RuntimeError: Android never becomes ready within the bounded boot interval.
    """
    ready = adb("shell", "getprop", "sys.boot_completed", check=False)
    if ready.returncode == 0 and ready.stdout.strip() == "1":
        print("Tablet is already running.", flush=True)
        return
    devices = command([str(SDK / "platform-tools/adb"), "devices"])
    present = any(
        line.startswith(SERIAL + "\t") for line in devices.stdout.splitlines()
    )
    if not present:
        print("Starting the Android tablet…", flush=True)
        log = (CACHE / "emulator.log").open("a")
        subprocess.Popen(
            [
                str(EMULATOR),
                "-avd",
                AVD,
                "-port",
                "5580",
                "-gpu",
                "swiftshader_indirect",
                "-feature",
                "-Vulkan",
                "-cores",
                "2",
                "-memory",
                "2048",
                "-no-audio",
                "-no-boot-anim",
                "-no-snapshot",
            ],
            env={**os.environ, "ANDROID_HOME": str(SDK)},
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        log.close()
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        result = adb("shell", "getprop", "sys.boot_completed", check=False)
        if result.returncode == 0 and result.stdout.strip() == "1":
            return
        time.sleep(2)
    raise RuntimeError(f"Tablet did not boot. See {CACHE / 'emulator.log'}")


def main() -> int:
    """Provide one-command build, boot, install and launch without manual Android work.

    Args:
        None; parses --rebuild, --stop and --stage-only from the command line.

    Returns:
        Zero on success; one with a concrete local diagnostic on failure.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rebuild", action="store_true")
    parser.add_argument("--stop", action="store_true")
    parser.add_argument("--stage-only", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        if args.stage_only:
            print(stage_sources())
            return 0
        for requirement in (FLET, EMULATOR, SDK / "platform-tools/adb"):
            if not requirement.exists():
                raise RuntimeError(
                    f"Demo setup is missing: {requirement}. "
                    f"See {PROTOTYPE / 'README.md'}"
                )
        if args.stop:
            adb("emu", "kill", check=False)
            print("Stopped the ErgoTools test tablet.")
            return 0
        build(args.rebuild)
        boot()
        apk_digest = hashlib.sha256(APK.read_bytes()).hexdigest()
        installed = CACHE / "installed_apk.sha256"
        present = adb("shell", "pm", "path", PACKAGE, check=False)
        if (
            present.returncode == 0
            and present.stdout.strip()
            and installed.exists()
            and installed.read_text() == apk_digest
        ):
            print("Current app is already installed; opening it.", flush=True)
        else:
            print("Installing updated app; saved tablet data is retained…", flush=True)
            print(adb("install", "-r", str(APK)).stdout.strip())
            installed.write_text(apk_digest)
        adb("shell", "am", "force-stop", PACKAGE)
        adb("shell", "am", "start", "-n", PACKAGE + "/.MainActivity")
        print("ErgoTools is open on the Android tablet.", flush=True)
        return 0
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
