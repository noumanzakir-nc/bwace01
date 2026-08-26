@echo off
setlocal enabledelayedexpansion

REM BW-ACE — Docker convenience launcher for Windows
REM Builds the image if it does not exist, then starts the container.
REM Usage: docker-run.bat [--build]

set IMAGE=bwace:latest
set CONTAINER=bwace

REM Check Docker is available.
REM Docker Desktop adds its bin dir to the USER PATH, which some terminal hosts
REM (VS Code, Explorer) don't inherit in the same process. Fall back to the
REM well-known per-user install location before giving up.
where docker >nul 2>nul
if errorlevel 1 (
    set "DOCKER_BIN=%LOCALAPPDATA%\Programs\DockerDesktop\resources\bin"
    if exist "!DOCKER_BIN!\docker.exe" (
        set "PATH=!DOCKER_BIN!;!PATH!"
    ) else (
        echo Docker was not found on PATH and was not found in the default
        echo Docker Desktop install location:
        echo   %LOCALAPPDATA%\Programs\DockerDesktop\resources\bin
        echo.
        echo Fixes:
        echo   1. Make sure Docker Desktop is installed and has been started at least once.
        echo   2. Open a NEW terminal after Docker Desktop finishes installing ^(PATH is set^).
        echo   3. Install from: https://www.docker.com/products/docker-desktop/
        exit /b 1
    )
)

REM Force a (re)build when --build is passed
if "%1"=="--build" (
    echo Building Docker image...
    docker build -t %IMAGE% .
    if errorlevel 1 (
        echo Image build failed.
        exit /b 1
    )
    goto :run
)

REM Build only if the image does not yet exist
docker image inspect %IMAGE% >nul 2>nul
if errorlevel 1 (
    echo Image not found — building for the first time...
    docker build -t %IMAGE% .
    if errorlevel 1 (
        echo Image build failed.
        exit /b 1
    )
)

:run
REM Remove a stopped container with the same name, if any
docker rm -f %CONTAINER% >nul 2>nul

REM Resolve env-file flag (optional)
set ENVFLAG=
if exist .env set ENVFLAG=--env-file .env

echo Starting BW-ACE ...
docker run --rm --name %CONTAINER% -p 8501:8501 %ENVFLAG% %IMAGE%

echo.
echo BW-ACE has stopped.
endlocal
