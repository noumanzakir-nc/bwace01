@echo off
setlocal enabledelayedexpansion

set MIN_MAJOR=3
set MIN_MINOR=11

where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found on PATH. Install Python %MIN_MAJOR%.%MIN_MINOR% or newer.
    exit /b 1
)

for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
for /f "tokens=1,2 delims=." %%a in ("%PYVER%") do (
    set FOUND_MAJOR=%%a
    set FOUND_MINOR=%%b
)

if %FOUND_MAJOR% LSS %MIN_MAJOR% (
    echo Found Python %PYVER%, but %MIN_MAJOR%.%MIN_MINOR%+ is required.
    exit /b 1
)
if %FOUND_MAJOR% EQU %MIN_MAJOR% if %FOUND_MINOR% LSS %MIN_MINOR% (
    echo Found Python %PYVER%, but %MIN_MAJOR%.%MIN_MINOR%+ is required.
    exit /b 1
)

if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
)

if not exist .venv\.provisioned (
    echo Installing dependencies...
    .venv\Scripts\python.exe -m pip install --quiet --upgrade pip
    .venv\Scripts\python.exe -m pip install --quiet -e .[dev]
    if errorlevel 1 (
        echo Dependency installation failed.
        exit /b 1
    )
    echo. > .venv\.provisioned
)

.venv\Scripts\streamlit.exe run src\bwace\app\main.py
