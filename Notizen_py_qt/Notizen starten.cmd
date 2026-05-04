@echo off
setlocal
set "APPDIR=%~dp0"
set "PYTHONPATH=%APPDIR%src;%PYTHONPATH%"
if not defined NOTIZEN_FORCE_VISIBLE set "NOTIZEN_FORCE_VISIBLE=1"
if not defined NOTIZEN_RESET_WINDOW set "NOTIZEN_RESET_WINDOW=1"
python -m notizen_py_qt --show --reset-window --no-tray %*
endlocal
