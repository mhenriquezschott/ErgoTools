@echo off
rem Desktop entry point for an initialized source checkout on Windows.
rem Arguments: forward the optional project path and launcher options unchanged.
rem Effects: launch the existing application; never install, update or save data.
rem Exit: propagate Python's exit code; retain the console after a startup failure.
setlocal
set "ergotools_python=%~dp0..\.venv\Scripts\python.exe"
if not exist "%ergotools_python%" (
    echo ErgoTools environment not found. Follow docs\installation.md first.
    pause
    exit /b 1
)
"%ergotools_python%" -m ergotools.launcher %*
set "ergotools_exit=%errorlevel%"
if not "%ergotools_exit%"=="0" pause
exit /b %ergotools_exit%
