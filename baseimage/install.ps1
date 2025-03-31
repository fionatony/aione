# AIONE Installation Script for Windows
function Install-Aione {
    # Function to pause before exit
    function Pause-And-Exit {
        param([int]$exitCode)
        Write-Host "`nPress Enter to continue..." -ForegroundColor Yellow
        Read-Host
        return $exitCode
    }

    # Store the original directory
    $originalLocation = Get-Location

    Write-Host "Starting AIONE Installation..." -ForegroundColor Green

    # Check if Docker is running
    try {
        $dockerInfo = docker info 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Docker is not running. Please start Docker Desktop and try again." -ForegroundColor Red
            return Pause-And-Exit 1
        }
        Write-Host "Docker is running" -ForegroundColor Green
    } catch {
        Write-Host "Docker is not installed or not running. Please install Docker Desktop and try again." -ForegroundColor Red
        return Pause-And-Exit 1
    }

    # Check for GPU support
    $hasGpu = $false
    try {
        $nvidiaSmi = nvidia-smi 2>&1
        if ($LASTEXITCODE -eq 0) {
            $hasGpu = $true
            Write-Host "NVIDIA GPU detected" -ForegroundColor Green
        } else {
            Write-Host "No NVIDIA GPU detected, will run without GPU acceleration" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "No NVIDIA GPU detected, will run without GPU acceleration" -ForegroundColor Yellow
    }

    # Check if git is installed
    try {
        $gitVersion = git --version
        Write-Host "Git is installed" -ForegroundColor Green
    } catch {
        Write-Host "Git is not installed. Please install Git and try again." -ForegroundColor Red
        return Pause-And-Exit 1
    }

    # Create temporary directory for cloning
    $tempDir = Join-Path $env:TEMP "aione-install"
    if (Test-Path $tempDir) {
        Remove-Item -Path $tempDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $tempDir | Out-Null

    # Clone repository
    Write-Host "Cloning AIONE repository..." -ForegroundColor Yellow
    git clone --config core.autocrlf=false --config core.eol=lf https://github.com/fionatony/aione.git $tempDir
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to clone repository" -ForegroundColor Red
        return Pause-And-Exit 1
    }

    # Change to baseimage directory
    Set-Location (Join-Path $tempDir "baseimage")

    # Build Docker image
    Write-Host "Building Docker image..." -ForegroundColor Yellow
    docker build -t aione:latest .
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to build Docker image" -ForegroundColor Red
        Set-Location $originalLocation
        return Pause-And-Exit 1
    }

    # Stop and remove existing container if it exists
    docker stop aione 2>$null
    docker rm aione 2>$null

    # Start container with GPU support if available
    Write-Host "Starting AIONE container..." -ForegroundColor Yellow
    $dockerRunCmd = "docker run -d --name aione -p 11434:11434 -p 5433:5433 -p 8081:8081 -p 7071:7071"
    if ($hasGpu) {
        $dockerRunCmd += " --rm --gpus all"
        Write-Host "Running with GPU support" -ForegroundColor Green
    }
    $dockerRunCmd += " aione:latest"
    
    Invoke-Expression $dockerRunCmd

    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to start container" -ForegroundColor Red
        Set-Location $originalLocation
        return Pause-And-Exit 1
    }

    # Return to original directory before cleanup
    Set-Location $originalLocation

    # Clean up temporary directory
    Remove-Item -Path $tempDir -Recurse -Force

    # Wait for services to start
    Write-Host "Waiting for services to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10

    # Open web interface
    Write-Host "Opening web interface..." -ForegroundColor Green
    Start-Process "http://localhost:7071"

    Write-Host @"
AIONE has been successfully installed and started!
Access the web interface at: http://localhost:7071
Services available:
   - Ollama API: http://localhost:11435
   - PostgreSQL: localhost:5433
   - Weaviate: http://localhost:8081
"@ -ForegroundColor Green

    return Pause-And-Exit 0
}

# Execute the installation
Install-Aione
