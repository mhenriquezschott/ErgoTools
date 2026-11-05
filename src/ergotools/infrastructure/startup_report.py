"""Bounded local startup reports and read-only operating-system display probes.

Infrastructure layer. JSON-lines reports contain platform/runtime/display diagnostics,
never assessment/database contents. Capture is optional and fail-soft: logging cannot
prevent startup. No DPI/scaling policy, package, project or system setting is changed.
"""

import ctypes
import json
import logging
import os
import platform
import re
import sys
import traceback
from collections.abc import Mapping
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from threading import RLock
from types import TracebackType
from uuid import uuid4


def diagnostics_default(platform_name: str) -> bool:
    """Choose owner-requested desktop trial defaults without persisting a preference.

    Args:
        platform_name: Python platform identity, normally sys.platform.

    Returns:
        True for Windows/macOS and False for Linux and other platforms.
    """
    return platform_name in ("win32", "darwin")


def diagnostics_directory(platform_name: str) -> Path:
    """Resolve a writable personal report directory independently of the checkout.

    Args:
        platform_name: Python platform identity.

    Returns:
        Windows LocalAppData, macOS Library/Logs or Linux XDG-state child directory.
        The directory is not created until reporting is explicitly enabled.
    """
    if platform_name == "win32":
        base = Path(
            os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData/Local")
        )
        return base / "ErgoTools/diagnostics"
    if platform_name == "darwin":
        return Path.home() / "Library/Logs/ErgoTools"
    return Path(
        os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local/state")
    ) / ("ergotools/diagnostics")


def system_details() -> dict[str, object]:
    """Collect a limited platform/version/environment inventory for display debugging.

    Args:
        None.

    Returns:
        JSON-compatible versions and explicitly allowlisted display environment values;
        no hostname, username, command arguments or complete environment dump.
    """
    packages: dict[str, str | None] = {}
    for name in (
        "ergotools",
        "PyQt5",
        "PyQt5-Qt5",
        "PyQt5-sip",
        "vtk",
        "highspy",
    ):
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = None
    keys = (
        "QT_QPA_PLATFORM",
        "QT_DEBUG_PLUGINS",
        "QT_SCALE_FACTOR",
        "QT_SCREEN_SCALE_FACTORS",
        "QT_AUTO_SCREEN_SCALE_FACTOR",
        "QT_ENABLE_HIGHDPI_SCALING",
        "QT_SCALE_FACTOR_ROUNDING_POLICY",
        "QT_FONT_DPI",
        "QT_DEVICE_PIXEL_RATIO",
        "QT_USE_PHYSICAL_DPI",
        "QT_OPENGL",
        "QT_ANGLE_PLATFORM",
        "QT_PLUGIN_PATH",
        "QT_QPA_PLATFORM_PLUGIN_PATH",
        "GDK_SCALE",
        "GDK_DPI_SCALE",
        "XDG_SESSION_TYPE",
        "DISPLAY",
        "WAYLAND_DISPLAY",
    )
    return {
        "os": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "python": sys.version,
        "python_executable": sys.executable,
        "pointer_bits": ctypes.sizeof(ctypes.c_void_p) * 8,
        "macos": platform.mac_ver()[0] or None,
        "windows": list(platform.win32_ver()) if sys.platform == "win32" else None,
        "packages": packages,
        "display_environment": {k: os.environ[k] for k in keys if k in os.environ},
    }


def windows_display_context(window_id: int | None = None) -> dict[str, object]:
    """Read native Windows awareness/DPI without setting an awareness context.

    Args:
        window_id: Existing native top-level handle, or None before windows exist.

    Returns:
        Available system/window DPI, awareness and remote-session values on Windows;
        empty elsewhere. Missing old-system APIs are recorded as unavailable.
    """
    if platform.system() != "Windows":
        return {}
    result: dict[str, object] = {}
    try:
        factory = getattr(ctypes, "WinDLL", None)
        if factory is None:
            return {"unavailable": "Windows DLL loader is unavailable"}
        user = factory("user32", use_last_error=True)
        user.GetSystemMetrics.argtypes = [ctypes.c_int]
        user.GetSystemMetrics.restype = ctypes.c_int
        result["remote_session"] = bool(user.GetSystemMetrics(0x1000))
        for name, args, result_type in (
            ("GetDpiForSystem", [], ctypes.c_uint),
            ("GetThreadDpiAwarenessContext", [], ctypes.c_void_p),
        ):
            try:
                function = getattr(user, name)
                function.argtypes = []
                function.restype = result_type
                value = function(*args)
                if name == "GetThreadDpiAwarenessContext":
                    awareness = user.GetAwarenessFromDpiAwarenessContext
                    awareness.argtypes = [ctypes.c_void_p]
                    awareness.restype = ctypes.c_int
                    result["thread_dpi_awareness"] = int(awareness(value))
                    try:
                        equal = user.AreDpiAwarenessContextsEqual
                        equal.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
                        equal.restype = ctypes.c_int
                        for key, label in (
                            (-1, "unaware"),
                            (-2, "system"),
                            (-3, "per_monitor"),
                            (-4, "per_monitor_v2"),
                            (-5, "unaware_gdi_scaled"),
                        ):
                            if equal(value, key):
                                result["thread_dpi_context"] = label
                                break
                    except (AttributeError, OSError) as error:
                        result["thread_dpi_context"] = {"unavailable": str(error)}
                else:
                    result["system_dpi"] = int(value)
            except (AttributeError, OSError) as error:
                result[name] = {"unavailable": str(error)}
        if window_id is not None:
            try:
                user.GetDpiForWindow.argtypes = [ctypes.c_void_p]
                user.GetDpiForWindow.restype = ctypes.c_uint
                result["window_dpi"] = int(user.GetDpiForWindow(window_id))
            except (AttributeError, OSError) as error:
                result["window_dpi"] = {"unavailable": str(error)}
    except (AttributeError, OSError) as error:
        result["unavailable"] = str(error)
    return result


class StartupReport(logging.Handler):
    """One bounded, thread-safe local JSONL report with restorable logging hooks."""

    def __init__(self, directory: Path, *, max_bytes: int = 2_000_000) -> None:
        """Create an exclusive report and prune only recognized older report sessions.

        Args:
            directory: Explicit personal/debug directory; never a project path.
            max_bytes: Per-file byte limit; one rotated sibling bounds each session.

        Returns:
            None; five sessions are retained, each at most two bounded files.

        Raises:
            OSError: The directory or initial exclusive report cannot be created.
            ValueError: The byte budget is smaller than the 256-byte event envelope.
        """
        if max_bytes < 256:
            raise ValueError("Diagnostic byte budget must be positive.")
        super().__init__(logging.DEBUG)
        self._installed = False
        directory.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        self.path = directory / f"ergotools-{stamp}-{uuid4().hex[:8]}.jsonl"
        self.path.touch(exist_ok=False)
        self.max_bytes, self._bytes = max_bytes, 0
        self._write_lock = RLock()
        self._startup_context: dict[str, Mapping[str, object]] = {}
        self._failed = False
        self._installed = False
        self._previous_level = logging.getLogger().level
        self._previous_exception = sys.excepthook
        pattern = r"ergotools-\d{8}T\d{12}Z-[0-9a-f]{8}\.jsonl"
        sessions = sorted(
            p for p in directory.iterdir() if re.fullmatch(pattern, p.name)
        )
        for old in sessions[:-5]:
            old.unlink(missing_ok=True)
            old.with_suffix(".jsonl.1").unlink(missing_ok=True)

    def record(self, event: str, fields: Mapping[str, object]) -> None:
        """Append one bounded event; an I/O failure disables capture without crashing.

        Args:
            event: Stable category identifying a startup/message/display observation.
            fields: Detached diagnostic fields, never a workspace or database object.

        Returns:
            None; oversized individual events are explicitly truncated. One rotated
            sibling preserves earlier context. Report failures print once to stderr.
        """
        if self._failed:
            return
        payload = {"utc": datetime.now(UTC).isoformat(), "event": event, **fields}
        line = (json.dumps(payload, ensure_ascii=False, default=str) + "\n").encode(
            "utf-8", errors="backslashreplace"
        )
        if len(line) > self.max_bytes:
            payload = {
                "utc": payload["utc"],
                "event": event,
                "truncated": True,
                "excerpt": line.decode()[: max(0, (self.max_bytes - 192) // 6)],
            }
            line = (json.dumps(payload, ensure_ascii=False) + "\n").encode(
                "utf-8", errors="backslashreplace"
            )
        try:
            with self._write_lock:
                if event in (
                    "process_start",
                    "qt_before_application",
                    "qt_application",
                    "screens",
                ):
                    self._startup_context[event] = dict(fields)
                if self._bytes + len(line) > self.max_bytes:
                    self.path.replace(self.path.with_suffix(".jsonl.1"))
                    self._bytes = 0
                    context = (
                        json.dumps(
                            {
                                "utc": payload["utc"],
                                "event": "startup_context",
                                "context": self._startup_context,
                            },
                            ensure_ascii=False,
                            default=str,
                        )
                        + "\n"
                    ).encode("utf-8", errors="backslashreplace")
                    if len(context) + len(line) <= self.max_bytes:
                        with self.path.open("ab") as stream:
                            stream.write(context)
                        self._bytes = len(context)
                with self.path.open("ab") as stream:
                    stream.write(line)
                    stream.flush()
                self._bytes += len(line)
        except OSError as error:
            self._failed = True
            print(f"ErgoTools diagnostics unavailable: {error}", file=sys.stderr)

    def emit(self, record: logging.LogRecord) -> None:
        """Capture Python diagnostics without removing the existing console handlers.

        Args:
            record: Standard-library logging event from this running application.

        Returns:
            None; exception context is retained while unrelated handlers still run.
        """
        self.record(
            "python_log",
            {
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "exception": "".join(traceback.format_exception(*record.exc_info))
                if record.exc_info
                else None,
            },
        )

    def install(self) -> None:
        """Install bounded capture and an uncaught-exception observer once.

        Args:
            None.

        Returns:
            None; normal console errors and the previous exception hook are preserved.
        """
        if self._installed:
            return
        self._installed = True
        logging.getLogger().addHandler(self)
        logging.getLogger().setLevel(logging.DEBUG)
        sys.excepthook = self.exception
        self.record("process_start", system_details())

    def exception(
        self,
        kind: type[BaseException],
        error: BaseException,
        trace: TracebackType | None,
    ) -> None:
        """Observe an uncaught error before delegating unchanged to the prior hook.

        Args:
            kind: Original exception class.
            error: Original exception value.
            trace: Original optional traceback.

        Returns:
            None; the prior hook retains its ordinary reporting/termination policy.
        """
        self.record(
            "uncaught_exception",
            {"traceback": "".join(traceback.format_exception(kind, error, trace))},
        )
        self._previous_exception(kind, error, trace)

    def close(self) -> None:
        """Restore only hooks owned by this report and release the logging handler.

        Args:
            None.

        Returns:
            None; no report, preference or project is removed on normal close.
        """
        if self._installed:
            logging.getLogger().removeHandler(self)
            logging.getLogger().setLevel(self._previous_level)
            if sys.excepthook == self.exception:
                sys.excepthook = self._previous_exception
            self._installed = False
        super().close()
