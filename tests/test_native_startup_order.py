"""Verify native solver initialization precedes Qt in fresh application processes.

Windows probe evidence isolates an access violation in automatic-thread MIP when
Qt is imported before highspy. A fresh interpreter is essential: the ordinary test
process has already cached Qt and cannot characterize this load-order contract.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("module", ["ergotools.launcher", "ergotools.bootstrap"])
def test_native_solver_loads_before_first_qt_import(module: str) -> None:
    """Run both real entry points with an import observer and ordinary CLI help.

    Args:
        module: Installed launcher or direct development composition entry point.

    Returns:
        None; real highspy is loaded before Qt, and help exits successfully without
        opening a project, creating windows or writing application preferences.
    """
    source = """
import builtins
import runpy
import sys
original_import = builtins.__import__
observed = []
def check_import(name, *args, **kwargs):
    if name == 'PyQt5' or name.startswith('PyQt5.'):
        assert 'highspy' in sys.modules, 'Qt loaded before native solver'
        observed.append(name)
    return original_import(name, *args, **kwargs)
builtins.__import__ = check_import
sys.argv = [sys.argv[1], '--help']
try:
    runpy.run_module(sys.argv[0], run_name='__main__')
except SystemExit as error:
    assert error.code == 0, error.code
assert observed, 'No Qt import observed; entry point was not exercised'
print('NATIVE_ORDER_OK')
"""
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    result = subprocess.run(
        [sys.executable, "-c", source, module],
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "NATIVE_ORDER_OK" in result.stdout
