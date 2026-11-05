"""Bounded optional diagnostics, native Qt read-only observation and CLI lifecycle.

Windows calls are controlled ABI-contract mocks on Linux, not native OS acceptance.
Every file is temporary. Real subprocesses exercise startup/shutdown and restored hooks.
"""

import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from PyQt5.QtCore import QCoreApplication, Qt, qWarning
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

from ergotools.infrastructure.startup_report import (
    StartupReport,
    diagnostics_default,
    diagnostics_directory,
    windows_display_context,
)
from ergotools.presentation.desktop.display_diagnostics import DisplayDiagnostics

# Retained native application for screen/geometry tests; subprocesses own separate apps.
_APP = QApplication.instance() or QApplication([])


@pytest.mark.parametrize(
    "platform,expected", [("linux", False), ("win32", True), ("darwin", True)]
)
def test_platform_policy_and_user_paths(
    platform: str, expected: bool, tmp_path: Path
) -> None:
    """Defaults are launch-local and directory lookup never creates files.

    Args:
        platform: Explicit platform policy identity, without pretending to run that OS.
        expected: Owner-requested automatic reporting state.
        tmp_path: Disposable environment root.

    Returns:
        None; checkout/CWD does not determine report placement.
    """
    assert diagnostics_default(platform) is expected
    with patch.dict(
        os.environ, {"LOCALAPPDATA": str(tmp_path), "XDG_STATE_HOME": str(tmp_path)}
    ):
        directory = diagnostics_directory(platform)
    assert directory.name in ("diagnostics", "ErgoTools")
    assert not (tmp_path / "ErgoTools").exists()


def test_bounded_unicode_reports_restore_hooks_and_preserve_unrelated_files(
    tmp_path: Path,
) -> None:
    """Rotation/retention stay bounded; logging and exception hooks are restored.

    Args:
        tmp_path: Disposable report directory with one unrelated user file.

    Returns:
        None; only report filenames are pruned; Unicode lines stay valid JSON.
    """
    untouched = tmp_path / "notes.jsonl"
    untouched.write_text("keep")
    before = sys.excepthook
    level = logging.getLogger().level
    report = StartupReport(tmp_path, max_bytes=800)
    report.install()
    logging.getLogger("ergotools.test").warning("Pantalla pequeña: ñ")
    for index in range(15):
        report.record("sample", {"index": index, "text": "áñ" * 2000})
    report.close()
    report.close()
    assert sys.excepthook is before and logging.getLogger().level == level
    assert report.path.stat().st_size <= 800
    assert report.path.with_suffix(".jsonl.1").stat().st_size <= 800
    records = [
        json.loads(line)
        for p in (report.path, report.path.with_suffix(".jsonl.1"))
        for line in p.read_text().splitlines()
    ]
    assert any(r.get("truncated") for r in records)
    for _ in range(7):
        StartupReport(tmp_path).close()
    assert len(list(tmp_path.glob("ergotools-*.jsonl"))) == 5
    assert untouched.read_text() == "keep"
    with pytest.raises(ValueError):
        StartupReport(tmp_path, max_bytes=0)


def test_report_failures_do_not_replace_exception_or_break_runtime(
    tmp_path: Path,
) -> None:
    """A failed write disables capture; prior exception handling is delegated.

    Args:
        tmp_path: Disposable report path.

    Returns:
        None; subsequent writes remain harmless after the first I/O failure.
    """
    previous = Mock()
    with patch.object(sys, "excepthook", previous):
        report = StartupReport(tmp_path)
        report.install()
        report.exception(ValueError, ValueError("test"), None)
        previous.assert_called_once()
        with patch.object(Path, "open", side_effect=OSError("disk unavailable")):
            report.record("failure", {})
            report.record("ignored", {})
        report.close()
    assert report._failed


def test_windows_api_contract_is_read_only_and_optional() -> None:
    """Mock available and missing Win32 readers without changing awareness anywhere.

    Args:
        None.

    Returns:
        None; unavailable calls are explicit and no SetDpi function is invoked.
    """
    api = SimpleNamespace(
        GetSystemMetrics=Mock(return_value=1),
        GetDpiForSystem=Mock(return_value=144),
        GetThreadDpiAwarenessContext=Mock(return_value=4),
        GetAwarenessFromDpiAwarenessContext=Mock(return_value=2),
        GetDpiForWindow=Mock(return_value=192),
        AreDpiAwarenessContextsEqual=Mock(side_effect=lambda value, key: key == -4),
    )
    with (
        patch(
            "ergotools.infrastructure.startup_report.platform.system",
            return_value="Windows",
        ),
        patch(
            "ergotools.infrastructure.startup_report.ctypes.WinDLL",
            return_value=api,
            create=True,
        ),
    ):
        result = windows_display_context(123)
        assert result == {
            "remote_session": True,
            "system_dpi": 144,
            "thread_dpi_awareness": 2,
            "thread_dpi_context": "per_monitor_v2",
            "window_dpi": 192,
        }
        api.GetDpiForWindow.assert_called_once_with(123)
        api.GetDpiForSystem.side_effect = OSError("old Windows")
        api.GetDpiForWindow.side_effect = OSError("unsupported")
        assert "unavailable" in windows_display_context(123)["window_dpi"]
    assert windows_display_context() == {}


def test_qt_capture_observes_screens_windows_messages_without_text_or_policy_changes(
    tmp_path: Path,
) -> None:
    """Actual Qt records DPI/layout/messages and safely skips deleted windows.

    Args:
        tmp_path: Private report directory.

    Returns:
        None; scale flags and widget geometry remain owned by the ordinary application.
    """
    flag = QCoreApplication.testAttribute(
        Qt.ApplicationAttribute.AA_EnableHighDpiScaling
    )
    report = StartupReport(tmp_path)
    observer = DisplayDiagnostics(report.record, lambda _: {})
    observer.attach(_APP)
    window = QWidget()
    layout = QVBoxLayout(window)
    layout.addWidget(QLabel("Private assessment text"))
    window.resize(400, 260)
    window.show()
    QTest.qWait(300)
    qWarning("Diagnostic test warning")
    window.resize(420, 280)
    QTest.qWait(300)
    observer.screen_added(_APP.primaryScreen())
    observer.close()
    observer.close()
    report.close()
    window.close()
    window.deleteLater()
    records = [json.loads(line) for line in report.path.read_text().splitlines()]
    events = {r["event"] for r in records}
    assert {
        "qt_before_application",
        "qt_application",
        "screens",
        "window_layout",
        "qt_message",
    } <= events
    assert "Private assessment text" not in report.path.read_text()
    screen = next(r["screens"][0] for r in records if r["event"] == "screens")
    assert screen["device_pixel_ratio"] > 0 and screen["logical_dpi"][0] > 0
    assert flag == QCoreApplication.testAttribute(
        Qt.ApplicationAttribute.AA_EnableHighDpiScaling
    )


@pytest.mark.parametrize(
    "mode",
    [
        "off",
        "on",
        "failure",
        "auto",
        "linux_default",
        "exception",
        "scaled",
        "scaled2",
        "probe_failure",
    ],
)
def test_real_desktop_startup_capture_is_optional_and_fail_soft(
    tmp_path: Path, mode: str
) -> None:
    """Run the actual bootstrap in an owned subprocess that closes after first show.

    Args:
        tmp_path: Disposable settings/report directory, never a maintained project.
        mode: Explicit disable, explicit enable, or unavailable-report destination.

    Returns:
        None; the desktop opens/closes and records data only when enabled.
    """
    directory = tmp_path / "reports"
    if mode == "failure":
        directory.write_text("not a directory")
    arguments = [
        "--integrated-preview",
        "--disable-vtk",
        "--settings",
        str(tmp_path / "prefs.json"),
    ]
    if mode == "off":
        arguments += ["--no-startup-diagnostics"]
    elif mode not in ("auto", "linux_default"):
        arguments += ["--diagnostics-dir", str(directory)]
    program = """
import sys
from PyQt5.QtCore import QTimer
from ergotools import bootstrap
original=bootstrap.create_window
def create(*args,**kwargs):
    window=original(*args,**kwargs)
    QTimer.singleShot(650,window.close)
    return window
bootstrap.create_window=create
from pathlib import Path
bootstrap.diagnostics_directory=lambda _:Path(REPORT_FOLDER)
if MODE in ('auto','off'):
    bootstrap.diagnostics_default=lambda _:True
if MODE=='linux_default':
    bootstrap.diagnostics_default=lambda _:False
if MODE=='probe_failure':
    def attach_failure(self,app):
        original_attach(self,app)
        raise RuntimeError('controlled probe failure')
    original_attach=bootstrap.DisplayDiagnostics.attach
    bootstrap.DisplayDiagnostics.attach=attach_failure
if MODE=='exception':
    def fail(*args,**kwargs):
        raise RuntimeError('controlled startup failure')
    bootstrap.create_window=fail
raise SystemExit(bootstrap.main(sys.argv[1:]))
"""
    program = program.replace("REPORT_FOLDER", repr(str(directory))).replace(
        "MODE", repr(mode)
    )
    environment = dict(os.environ)
    if mode in ("scaled", "scaled2"):
        environment["QT_SCALE_FACTOR"] = "1.5" if mode == "scaled" else "2"
    result = subprocess.run(
        [sys.executable, "-c", program, *arguments],
        capture_output=True,
        text=True,
        timeout=30,
        env=environment,
    )
    assert result.returncode == (1 if mode == "exception" else 0), result.stderr
    if mode in ("on", "auto", "exception", "scaled", "scaled2", "probe_failure"):
        path = next(directory.glob("*.jsonl"))
        records = [json.loads(line) for line in path.read_text().splitlines()]
        if mode == "probe_failure":
            assert any(r["event"] == "qt_probe_unavailable" for r in records)
            return
        if mode == "exception":
            assert any(r["event"] == "startup_exception" for r in records)
            return
        if mode in ("scaled", "scaled2"):
            expected = 1.5 if mode == "scaled" else 2
            screens = next(r["screens"] for r in records if r["event"] == "screens")
            assert screens[0]["device_pixel_ratio"] == pytest.approx(expected)
        assert {"process_start", "qt_application", "window_layout", "process_end"} <= {
            r["event"] for r in records
        }
    elif mode in ("off", "linux_default"):
        assert not directory.exists()
    else:
        assert "diagnostics unavailable" in result.stderr
