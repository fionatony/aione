#!/bin/bash

echo "Checking for NVIDIA GPU..."
if command -v nvidia-smi &> /dev/null; then
    if nvidia-smi &> /dev/null; then
        echo "NVIDIA GPU detected! Building with GPU support..."
        GPU_PARAMS="--gpus all"
    else
        echo "No NVIDIA GPU detected or nvidia-smi not available."
        echo "If you have an NVIDIA GPU installed, please make sure:"
        echo "  - NVIDIA drivers are properly installed"
        echo "  - NVIDIA CUDA Toolkit is installed"
        echo "  - nvidia-smi executable is in your PATH"
        GPU_PARAMS=""
    fi
else
    echo "No NVIDIA GPU detected or nvidia-smi not available."
    echo "If you have an NVIDIA GPU installed, please make sure:"
    echo "  - NVIDIA drivers are properly installed"
    echo "  - NVIDIA CUDA Toolkit is installed"
    echo "  - nvidia-smi executable is in your PATH"
    GPU_PARAMS=""
fi

echo "Building AIONE Docker image..."
docker build -t aione:latest .

if [ $? -eq 0 ]; then
    echo "Build successful!"
    
    echo "Removing existing container if it exists..."
    docker rm -f aione &> /dev/null
    
    echo "Running AIONE container..."
    docker run -d --name aione \
        $GPU_PARAMS \
        -p 11434:11434 \
        -p 5433:5433 \
        -p 8081:8081 \
        -p 7071:7071 \
        aione:latest
    
    echo "AIONE is now running!"
    echo "Available services:"
    echo "- Ollama API: http://localhost:11434"
    echo "- PostgreSQL: localhost:5433"
    echo "- Weaviate: http://localhost:8081"
    echo "- Web Interface: http://localhost:7071"
    if [ "$GPU_PARAMS" = "--gpus all" ]; then
        echo
        echo "GPU support is enabled!"
    fi
    echo
    echo "Container management commands:"
    echo "- View logs: docker logs -f aione"
    echo "- Stop container: docker stop aione"
    echo "- Remove container: docker rm aione"
else
    echo "Build failed!"
fi 