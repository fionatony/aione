# Ollama Web Interface

A modern web interface for managing and interacting with [Ollama](https://ollama.ai/) models, built with Flask and a modular architecture.

## Features

1. **Model Management**
   - View all installed models
   - Browse available models from a curated list
   - Install new models with progress tracking
   - Delete existing models
   - Real-time installation progress monitoring

2. **System Information**
   - GPU status and information
   - System health monitoring
   - Ollama server connection status

3. **Chat Interface**
   - Select any installed model
   - Real-time chat with models
   - Modern, responsive UI

4. **Terminal Interface**
   - Execute Ollama commands directly
   - View command output in real-time
   - Command history support

## Technical Stack

- **Backend**: Flask 2.2.3
- **Frontend**: Modern web technologies
- **Dependencies**:
  - Flask 2.2.3
  - Requests 2.28.2
  - Python-dotenv 0.21.1
  - Werkzeug 2.2.3

## Installation

### Requirements

- Python 3.7+
- Ollama (running locally or in a Docker container)

### Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Configure environment variables (optional):

```
OLLAMA_HOST=localhost  # Hostname of Ollama server
OLLAMA_PORT=11434     # Port of Ollama server
APP_PORT=7071         # Port for the web interface
LOG_LEVEL=INFO        # Logging level (DEBUG, INFO, WARNING, ERROR)
```

3. Run the application:

```bash
python app.py
```

Or with custom options:

```bash
python app.py --port 7071 --host 0.0.0.0 --debug
```

4. Access the web interface at `http://localhost:7071`

## API Endpoints

- `GET /api/models` - List installed models
- `GET /api/models/available` - List available models from models.json
- `POST /api/models/install` - Install a new model
- `POST /api/models/delete` - Delete a model
- `GET /api/models/progress` - Get installation progress
- `POST /api/terminal/execute` - Execute terminal commands
- `POST /api/chat` - Send chat messages to models
- `GET /api/system/gpu` - Get GPU information
- `GET /health` - Health check endpoint

## Development

The project follows a modular architecture:
- `modules/` - Core functionality modules
- `templates/` - HTML templates
- `static/` - Static assets
- `models.json` - Available models configuration

## License

MIT 