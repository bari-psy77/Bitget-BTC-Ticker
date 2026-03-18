@echo off
setlocal
cd /d %~dp0

set "PYTHON_EXE=pythonw"
if exist ".venv\Scripts\pythonw.exe" set "PYTHON_EXE=.venv\Scripts\pythonw.exe"
if exist "venv\Scripts\pythonw.exe" set "PYTHON_EXE=venv\Scripts\pythonw.exe"

"%PYTHON_EXE%" -m bitget_ticker.main
if errorlevel 1 (
  echo GUI 실행에 실패했습니다. 콘솔 Python으로 다시 시도합니다.
  python -m bitget_ticker.main
  pause
)
