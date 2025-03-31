# AIONE - AI One Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://www.docker.com/)
[![GPU Support](https://img.shields.io/badge/GPU-Accelerated-green)](https://github.com/NVIDIA/nvidia-container-toolkit)

AIONE (AI One) is a collection of pre-made Docker images designed to simplify AI development and deployment. Each image is carefully crafted to provide a complete environment for specific AI development needs.

## Pre-made Images

### 1. Base Image
The foundation of AIONE, combining essential services for AI development:

- **Ollama**: AI model management and inference
- **Weaviate**: Vector database for semantic search
- **PostgreSQL**: Structured data storage
- **GPU Acceleration**: Built-in NVIDIA GPU support
- **Web Interface**: Modern UI for model management

**Docker Hub**: [aione/baseimage](https://hub.docker.com/r/aione/baseimage)

**Quick Start**:
```bash
docker pull aione/baseimage:latest
docker run -d --name aione --gpus all -p 11435:11435 -p 5433:5433 -p 8081:8081 -p 7071:7071 aione/baseimage:latest
```

### More Images Coming Soon
- [ ] Data Science Image
- [ ] Computer Vision Image
- [ ] NLP Image
- [ ] Reinforcement Learning Image

## Features

- **Easy Setup**: One-click installation scripts for Windows, Mac, and Linux
- **GPU Support**: Automatic detection and utilization of NVIDIA GPUs
- **Real-time Monitoring**: Visual display of GPU usage and system metrics
- **Flexible Deployment**: Run on both GPU and CPU-only environments
- **Modern UI**: Responsive web interface for all operations

## Quick Start

### Prerequisites
- Docker installed and running
- 4GB+ RAM (8GB+ recommended)
- 10GB+ free disk space
- NVIDIA GPU (optional, for GPU support)

### Installation

#### Windows (PowerShell)
```powershell
irm "https://raw.githubusercontent.com/fionatony/aione/main/baseimage/install.ps1" | iex
```

#### Linux/Mac
```bash
curl -sSL "https://raw.githubusercontent.com/fionatony/aione/main/baseimage/install.sh" | bash
```

## Documentation

For detailed documentation, visit our [documentation site](https://github.com/fionatony/aione/tree/main/docs).

## Contributing

We welcome contributions! Please see our [contributing guidelines](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Links

- [GitHub Repository](https://github.com/fionatony/aione)
- [Docker Hub](https://hub.docker.com/r/aione)
- [Documentation](https://github.com/fionatony/aione/tree/main/docs)
- [Issues](https://github.com/fionatony/aione/issues) 