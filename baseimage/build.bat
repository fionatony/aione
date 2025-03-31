@echo off
echo Checking for Docker installation...
docker --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Docker is not installed or not in PATH
    echo Please install Docker Desktop for Windows from https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo Checking for NVIDIA GPU...
nvidia-smi >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo NVIDIA GPU detected! Building with GPU support...
    set GPU_PARAMS=--gpus all
) else (
    echo No NVIDIA GPU detected or nvidia-smi not available.
    echo If you have an NVIDIA GPU installed, please make sure:
    echo  - NVIDIA drivers are properly installed
    echo  - NVIDIA CUDA Toolkit is installed
    echo  - nvidia-smi executable is in your PATH
    set GPU_PARAMS=
)

echo Checking port availability...
netstat -ano | find ":11434" >nul
if %ERRORLEVEL% EQU 0 (
    echo Error: Port 11434 is already in use
    echo Please ensure no other service is using this port
    pause
    exit /b 1
)

echo Building AIONE Docker image...
docker build -t aione:latest .

if %ERRORLEVEL% EQU 0 (
    echo Build successful!
    
    echo Removing existing container if it exists...
    docker rm -f aione >nul 2>&1
    
    echo Running AIONE container...
    docker run -d --name aione ^
        %GPU_PARAMS% ^
        -p 11434:11434 ^
        -p 5433:5433 ^
        -p 8081:8081 ^
        -p 7071:7071 ^
        aione:latest
    
    echo AIONE is now running!
    echo Available services:
    echo - Ollama API: http://localhost:11434
    echo - PostgreSQL: localhost:5433
    echo - Weaviate: http://localhost:8081
    echo - Web Interface: http://localhost:7071
    if "%GPU_PARAMS%"=="--gpus all" (
        echo.
        echo GPU support is enabled!
    )
    echo.
    echo Container management commands:
    echo - View logs: docker logs -f aione
    echo - Stop container: docker stop aione
    echo - Remove container: docker rm aione
) else (
    echo Build failed!
)
pause 