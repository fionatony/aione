#!/bin/bash

# AIONE Installation Script for Linux and macOS
echo "🚀 Starting AIONE Installation..."

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    OPEN_CMD="open"
    TEMP_DIR=$(mktemp -d -t aione)
else
    OS="linux"
    OPEN_CMD="xdg-open"
    TEMP_DIR=$(mktemp -d)
fi

# Store the original directory
ORIGINAL_DIR=$(pwd)

# Function to handle errors and cleanup
cleanup() {
    cd "$ORIGINAL_DIR"
    if [ -d "$TEMP_DIR" ]; then
        rm -rf "$TEMP_DIR"
    fi
    exit "$1"
}

# Set up trap for cleanup on script exit
trap 'cleanup $?' EXIT

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    if [ "$OS" = "macos" ]; then
        echo "ℹ️ On macOS, make sure Docker Desktop is running"
    fi
    cleanup 1
fi
echo "✅ Docker is running"

# Check for GPU support
if command -v nvidia-smi &> /dev/null && nvidia-smi > /dev/null 2>&1; then
    echo "✅ NVIDIA GPU detected"
    GPU_ARG="--gpus all"
else
    echo "ℹ️ No NVIDIA GPU detected, running without GPU acceleration"
    GPU_ARG=""
fi

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git and try again."
    if [ "$OS" = "macos" ]; then
        echo "ℹ️ On macOS, you can install Git using: brew install git"
    fi
    cleanup 1
fi
echo "✅ Git is installed"

# Create and enter temporary directory
cd "$TEMP_DIR" || cleanup 1

# Clone repository
echo "📥 Cloning AIONE repository..."
if ! git clone --config core.autocrlf=false --config core.eol=lf https://github.com/fionatony/aione.git .; then
    echo "❌ Failed to clone repository"
    cleanup 1
fi

# Change to baseimage directory
cd baseimage || cleanup 1

# Build Docker image
echo "🏗️ Building Docker image..."
if ! docker build -t aione:latest .; then
    echo "❌ Failed to build Docker image"
    cleanup 1
fi

# Stop and remove existing container if it exists
docker stop aione 2>/dev/null || true
docker rm aione 2>/dev/null || true

# Start container with appropriate GPU settings
echo "🚀 Starting AIONE container..."
if ! docker run -d --name aione $GPU_ARG -p 11434:11434 -p 5433:5433 -p 8081:8081 -p 7071:7071 aione:latest; then
    echo "❌ Failed to start container"
    cleanup 1
fi

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Print access information
echo -e "\n✅ AIONE has been successfully installed and started!"
echo "📝 Access the web interface at: http://localhost:7071"
echo "🔧 Services available:"
echo "   - Ollama API: http://localhost:11434"
echo "   - PostgreSQL: localhost:5433"
echo "   - Weaviate: http://localhost:8081"

# Open web interface based on OS
echo -e "\nOpening web interface..."
if command -v $OPEN_CMD &> /dev/null; then
    $OPEN_CMD "http://localhost:7071"
else
    echo "ℹ️ Could not automatically open the web interface."
    echo "Please open http://localhost:7071 in your browser manually."
fi

# Return to original directory
cd "$ORIGINAL_DIR"

# Cleanup temporary directory
rm -rf "$TEMP_DIR"

exit 0 