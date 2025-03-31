from flask import Flask, jsonify, request, render_template, redirect, url_for
import os
import requests
import json
import logging
from typing import Dict, List, Optional
import argparse

# Import local modules
from modules.ollama_manager import OllamaManager

# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Global variables from environment
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'localhost')
OLLAMA_PORT = int(os.getenv('OLLAMA_PORT', '11434'))
APP_PORT = int(os.getenv('APP_PORT', '7071'))  # Match the port in start.sh

# For container setups, localhost may need to be 0.0.0.0 or 127.0.0.1
# When running inside the same container as Ollama, use localhost
# Don't include port in OLLAMA_HOST if it will be managed separately
logger.info(f"Configured OLLAMA_HOST={OLLAMA_HOST} and OLLAMA_PORT={OLLAMA_PORT}")

# Initialize managers
ollama_manager = OllamaManager(host=OLLAMA_HOST, port=OLLAMA_PORT)

# Create Flask app
app = Flask(__name__)

# Routes
@app.route('/')
def index():
    """Render main UI page"""
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok"})

@app.route('/api/models', methods=['GET'])
def get_models():
    """Get the list of installed models"""
    try:
        models = ollama_manager.get_models(force_refresh=True)
        return jsonify({"models": models})
    except Exception as e:
        logger.error(f"Error getting models: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/models/available', methods=['GET'])
def get_available_models():
    """Get the list of available models from models.json"""
    try:
        models_json_path = os.path.join(app.root_path, 'models.json')
        
        if os.path.exists(models_json_path):
            with open(models_json_path, 'r') as f:
                models_data = json.load(f)
            return jsonify(models_data)
        else:
            logger.error(f"models.json file not found at {models_json_path}")
            return jsonify({"error": "Models list not found"}), 404
    except Exception as e:
        logger.error(f"Error loading available models: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/models/install', methods=['POST'])
def install_model():
    """Install a model"""
    data = request.json
    model_name = data.get('model')
    
    if not model_name:
        return jsonify({"error": "Model name is required"}), 400
    
    try:
        result = ollama_manager.pull_model(model_name)
        return jsonify({"message": result})
    except Exception as e:
        logger.error(f"Error installing model: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/models/delete', methods=['POST'])
def delete_model():
    """Delete a model"""
    data = request.json
    model_name = data.get('model')
    
    if not model_name:
        return jsonify({"error": "Model name is required"}), 400
    
    try:
        result = ollama_manager.delete_model(model_name)
        return jsonify({"message": result})
    except Exception as e:
        logger.error(f"Error deleting model: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/models/progress', methods=['GET'])
def get_progress():
    """Get the installation progress"""
    try:
        # Add a caching header for empty responses
        progress = ollama_manager.get_installation_progress()
        
        # If there's nothing happening, add Cache-Control header to reduce load
        response = jsonify(progress)
        if not progress.get('in_progress') and not progress.get('status') and not progress.get('progress'):
            # Allow caching for 10 seconds when nothing is happening
            response.headers['Cache-Control'] = 'max-age=10'
        else:
            # No caching for active installations
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        
        return response
    except Exception as e:
        logger.error(f"Error getting progress: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/terminal/execute', methods=['POST'])
def execute_command():
    """Execute a terminal command"""
    data = request.json
    command = data.get('command')
    
    if not command:
        return jsonify({"error": "Command is required"}), 400
    
    try:
        result = ollama_manager.execute_command(command)
        return jsonify({"output": result})
    except Exception as e:
        logger.error(f"Error executing command: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Send a chat message to a model"""
    data = request.json
    model = data.get('model')
    message = data.get('message')
    
    if not model or not message:
        return jsonify({"error": "Model and message are required"}), 400
    
    try:
        response = ollama_manager.chat(model, message)
        return jsonify({"response": response})
    except Exception as e:
        logger.error(f"Error chatting with model: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/system/gpu', methods=['GET'])
def get_gpu_info():
    """Get GPU information"""
    try:
        gpu_info = ollama_manager.get_gpu_info()
        return jsonify(gpu_info)
    except Exception as e:
        logger.error(f"Error getting GPU info: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Entry point
if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Ollama Web Interface')
    parser.add_argument('--port', type=int, default=APP_PORT, help='Port to run the server on')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to run the server on')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    args = parser.parse_args()
    
    # Log startup information
    logger.info(f"Starting web server on {args.host}:{args.port}")
    logger.info(f"Ollama configured at {OLLAMA_HOST}:{OLLAMA_PORT}")
    
    try:
        # Run the Flask application
        app.run(debug=args.debug, host=args.host, port=args.port)
    except Exception as e:
        logger.error(f"Failed to start web server: {str(e)}")
        raise 