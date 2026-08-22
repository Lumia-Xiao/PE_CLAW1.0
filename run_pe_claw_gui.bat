@echo off
setlocal
cd /d "%~dp0"

if defined PE_CLAW_PYTHON (
    set "PYTHON_EXE=%PE_CLAW_PYTHON%"
) else if exist "%CD%\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%CD%\.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
    where python >nul 2>&1
    if errorlevel 1 (
        echo PE-Claw requires Python 3.10 or newer.
        echo Install Python with Tkinter support, or set PE_CLAW_PYTHON to python.exe.
        pause
        exit /b 1
    )
)

"%PYTHON_EXE%" "%CD%\scripts\check_runtime_dependencies.py"
if errorlevel 1 (
    echo.
    echo Install the required packages with:
    echo   "%PYTHON_EXE%" -m pip install -r "%CD%\requirements.txt"
    pause
    exit /b 1
)

set "PYTHONPATH=%CD%\src;%PYTHONPATH%"
if defined PE_CLAW_STARTUP_CHECK (
    "%PYTHON_EXE%" -c "import pe_claw_gui; from pe_claw_gui.app.shell.main_window import PEClawMainWindow; app=PEClawMainWindow(); app.withdraw(); app.update_idletasks(); app.destroy(); print('PE-Claw GUI startup import check passed:', pe_claw_gui.__file__)"
    if errorlevel 1 exit /b 1
    exit /b 0
)

echo Starting PE-Claw GUI with "%PYTHON_EXE%"
"%PYTHON_EXE%" -m pe_claw_gui
if errorlevel 1 (
    echo.
    echo PE-Claw GUI failed to start. Make sure Python 3.10+ and project dependencies are available.
    pause
)
