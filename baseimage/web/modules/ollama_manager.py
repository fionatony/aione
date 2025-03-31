import requests
import logging
import time
import subprocess
import threading
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any
import json

# Set up logging
logger = logging.getLogger(__name__)

class OllamaManager:
    """Class to manage Ollama models, terminal commands, and chat"""
    
    def __init__(self, host: str = 'localhost', port: int = 11434):
        """Initialize the Ollama manager
        
        Args:
            host: Hostname of Ollama server
            port: Port of Ollama server
        """
        self.host = host
        self.port = port
        
        # Fix URL construction to handle hosts that might already include a port
        if ':' in host:
            # If host already contains a port, use it as is
            self.base_url = f"http://{host}"
            logger.info(f"Using host with provided port: {self.base_url}")
        else:
            # If no port in host, append the port
            self.base_url = f"http://{host}:{port}"
            logger.info(f"Using host with port: {self.base_url}")
            
        self.models_cache = None
        self.models_last_updated = 0
        self.cache_ttl = 30  # 30 seconds cache TTL
        self.installation_in_progress = False
        self.installation_status = ""
        self.installation_progress = ""
        self.command_history = []
        self.max_history = 20
        self.lock = threading.Lock()
        
    def get_models(self, force_refresh: bool = False) -> List[Dict]:
        """Get list of all models
        
        Args:
            force_refresh: Force a refresh of the models cache
            
        Returns:
            List of model information dictionaries
        """
        current_time = time.time()
        
        # Check if we need to refresh the cache
        if (
            force_refresh or 
            self.models_cache is None or 
            current_time - self.models_last_updated > self.cache_ttl
        ):
            try:
                response = requests.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    models_data = response.json().get("models", [])
                    
                    # Format model information
                    for model in models_data:
                        # Format model size
                        size_bytes = model.get("size", 0)
                        model["size_formatted"] = self._format_size(size_bytes)
                        
                        # Format date
                        if "modified_at" in model:
                            timestamp = model.get("modified_at")
                            try:
                                dt = datetime.fromtimestamp(timestamp)
                                model["modified_at_formatted"] = dt.strftime("%Y-%m-%d %H:%M:%S")
                            except Exception:
                                model["modified_at_formatted"] = "Unknown"
                                
                    self.models_cache = models_data
                    self.models_last_updated = current_time
                    return models_data
                else:
                    logger.error(f"Failed to get models: {response.status_code}")
                    return self.models_cache or []
            except Exception as e:
                logger.error(f"Error getting models: {str(e)}")
                return self.models_cache or []
        else:
            return self.models_cache
    
    def get_model_names(self) -> List[str]:
        """Get list of all model names
        
        Returns:
            List of model names
        """
        models = self.get_models()
        return [model.get("name") for model in models]
    
    def pull_model(self, model_name: str) -> str:
        """Pull a model from Ollama
        
        Args:
            model_name: Name of the model to pull
            
        Returns:
            Status message
        """
        if self.installation_in_progress:
            return f"Installation already in progress. Please wait."
            
        self.installation_in_progress = True
        self.installation_status = f"Installing {model_name}..."
        self.installation_progress = "0%"
        
        # Start a background thread for the installation
        thread = threading.Thread(
            target=self._pull_model_thread,
            args=(model_name,)
        )
        thread.daemon = True
        thread.start()
        
        return f"Started installing {model_name}. This may take several minutes."
        
    def _pull_model_thread(self, model_name: str) -> None:
        """Thread function to pull a model
        
        Args:
            model_name: Name of the model to pull
        """
        try:
            # Use Ollama API to pull the model with streaming enabled
            with requests.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name, "stream": True},  # Enable streaming for progress updates
                stream=True,  # Enable streaming in requests
                timeout=3600  # 1 hour timeout
            ) as response:
                if response.status_code == 200:
                    total_size = 0
                    downloaded = 0
                    
                    # Process the streaming response line by line
                    for line in response.iter_lines():
                        if line:
                            try:
                                # Parse the JSON line
                                progress_data = json.loads(line)
                                
                                # Check for completion
                                if progress_data.get("status") == "success":
                                    self.installation_status = f"Successfully installed {model_name}"
                                    self.installation_progress = "100% - Complete"
                                    logger.info(f"Successfully installed model: {model_name}")
                                    
                                    # Start a timer to clear the status after completion
                                    status_clear_timer = threading.Timer(
                                        10.0,  # Clear status after 10 seconds
                                        self._clear_installation_status
                                    )
                                    status_clear_timer.daemon = True
                                    status_clear_timer.start()
                                    break
                                
                                # Update progress based on download information
                                if "total" in progress_data:
                                    total_size = progress_data.get("total", 0)
                                
                                if "completed" in progress_data:
                                    downloaded = progress_data.get("completed", 0)
                                    if total_size > 0:
                                        percent = int((downloaded / total_size) * 100)
                                        self.installation_progress = f"{percent}%"
                                        self.installation_status = f"Installing {model_name}... ({self._format_size(downloaded)} of {self._format_size(total_size)})"
                                        logger.info(f"Download progress for {model_name}: {percent}%")
                                
                                # Handle digest pulling message
                                if progress_data.get("status") == "pulling digest":
                                    digest = progress_data.get("digest", "")
                                    if digest:
                                        self.installation_status = f"Pulling digest for {model_name}: {digest}"
                                        logger.info(f"Pulling digest: {digest}")
                            except json.JSONDecodeError:
                                # Skip lines that aren't valid JSON
                                pass
                            except Exception as e:
                                logger.error(f"Error processing progress update: {str(e)}")
                    
                    # Final check - if we have a non-100% progress but finished successfully
                    if not self.installation_progress.startswith("100%"):
                        self.installation_status = f"Successfully installed {model_name}"
                        self.installation_progress = "100% - Complete"
                        logger.info(f"Installation of {model_name} completed")
                        
                        # Start a timer to clear the status after completion
                        status_clear_timer = threading.Timer(
                            10.0,  # Clear status after 10 seconds
                            self._clear_installation_status
                        )
                        status_clear_timer.daemon = True
                        status_clear_timer.start()
                else:
                    error_msg = f"Failed to install {model_name}: {response.status_code}"
                    self.installation_status = error_msg
                    self.installation_progress = "Failed"
                    logger.error(error_msg)
                    
                    try:
                        error_text = response.text
                        if error_text:
                            self.installation_status = f"Failed to install {model_name}: {error_text}"
                            logger.error(f"Error response: {error_text}")
                    except Exception:
                        pass
                    
                    # Start a timer to clear the error status
                    status_clear_timer = threading.Timer(
                        30.0,  # Clear error status after 30 seconds
                        self._clear_installation_status
                    )
                    status_clear_timer.daemon = True
                    status_clear_timer.start()
        except Exception as e:
            error_msg = f"Error installing {model_name}: {str(e)}"
            self.installation_status = error_msg
            self.installation_progress = "Failed"
            logger.error(error_msg)
            
            # Start a timer to clear the error status
            status_clear_timer = threading.Timer(
                30.0,  # Clear error status after 30 seconds
                self._clear_installation_status
            )
            status_clear_timer.daemon = True
            status_clear_timer.start()
        finally:
            # Ensure we always mark installation as complete
            self.installation_in_progress = False
    
    def _clear_installation_status(self):
        """Clear installation status and progress"""
        logger.info("Clearing installation status and progress")
        self.installation_status = ""
        self.installation_progress = ""
        self.installation_in_progress = False
    
    def get_installation_progress(self) -> Dict[str, Any]:
        """Get the current installation progress
        
        Returns:
            Dict with status and progress information
        """
        # Only include detailed information if there's an active installation or status has been set
        if self.installation_in_progress or self.installation_status or self.installation_progress:
            return {
                "status": self.installation_status,
                "progress": self.installation_progress,
                "in_progress": self.installation_in_progress
            }
        else:
            # Return a minimal response when nothing is happening
            # This helps reduce unnecessary data transfer for frequent polling
            return {
                "in_progress": False
            }
    
    def delete_model(self, model_name: str) -> str:
        """Delete a model from Ollama
        
        Args:
            model_name: Name of the model to delete
            
        Returns:
            Status message
        """
        try:
            response = requests.delete(
                f"{self.base_url}/api/delete",
                json={"name": model_name}
            )
            
            if response.status_code == 200:
                return f"Successfully deleted {model_name}"
            else:
                return f"Failed to delete {model_name}: {response.status_code}"
        except Exception as e:
            logger.error(f"Error deleting model {model_name}: {str(e)}")
            return f"Error deleting model: {str(e)}"
    
    def execute_command(self, command: str, timeout: int = 30) -> str:
        """Execute a command in the terminal
        
        Args:
            command: Command to execute
            timeout: Timeout in seconds (default: 30)
            
        Returns:
            Command output
        """
        if not command or command.strip() == "":
            return "No command specified"
            
        command = command.strip()
        logger.info(f"Executing command: {command}")
        
        # Record the command in history
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            # Execute the command
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for the command to complete with timeout
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                exit_code = process.returncode
                
                # Process output
                output = ""
                if stdout:
                    output += stdout
                if stderr:
                    if output:
                        output += "\n\nERROR:\n"
                    output += stderr
                    
                status = "SUCCESS" if exit_code == 0 else "ERROR"
                self._add_to_history(command, status, timestamp)
                
                logger.info(f"Command completed with exit code {exit_code}")
                return f"Exit Code: {exit_code}\n\n{output}"
                
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                self._add_to_history(command, "TIMEOUT", timestamp)
                
                logger.warning(f"Command timed out after {timeout} seconds: {command}")
                return f"Command timed out after {timeout} seconds"
                
        except Exception as e:
            self._add_to_history(command, "ERROR", timestamp)
            logger.error(f"Error executing command: {str(e)}")
            return f"Error executing command: {str(e)}"
    
    def _add_to_history(self, command: str, status: str, timestamp: str) -> None:
        """Add a command to history
        
        Args:
            command: Command that was executed
            status: Command status (SUCCESS, ERROR, etc.)
            timestamp: Timestamp when the command was executed
        """
        # Add to beginning of list
        with self.lock:
            self.command_history.insert(0, [command, status, timestamp])
            
            # Trim history if needed
            if len(self.command_history) > self.max_history:
                self.command_history = self.command_history[:self.max_history]
    
    def get_command_history(self) -> List[List[str]]:
        """Get command history
        
        Returns:
            List of [command, status, timestamp] lists
        """
        with self.lock:
            return self.command_history
    
    def chat(self, model: str, message: str) -> str:
        """Send a chat message to a model
        
        Args:
            model: Model name
            message: User message
            
        Returns:
            Model response
        """
        try:
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": message
                    }
                ],
                "stream": False  # Ensure we get a complete response, not a stream
            }
            
            logger.info(f"Sending chat request to {self.base_url}/api/chat for model {model}")
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            
            if response.status_code == 200:
                try:
                    response_json = response.json()
                    return response_json.get("message", {}).get("content", "")
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {str(e)}, Response content: {response.text[:200]}...")
                    
                    # Try to extract content by parsing the response text directly
                    if '"content":' in response.text:
                        try:
                            # Find the content section
                            content_start = response.text.find('"content":') + len('"content":')
                            # Find the next quote after "content":
                            quote_pos = response.text.find('"', content_start)
                            if quote_pos > 0:
                                content_start = quote_pos + 1
                                # Find the closing quote
                                content_end = response.text.find('"', content_start)
                                if content_end > 0:
                                    return response.text[content_start:content_end]
                        except Exception as parse_err:
                            logger.error(f"Error parsing response content: {str(parse_err)}")
                    
                    # Fallback to returning the first 1000 characters of the response
                    return f"Response could not be parsed as JSON. Raw response: {response.text[:1000]}..."
            else:
                logger.error(f"Error in chat response: {response.status_code}")
                return f"Error: Failed to get response from model. Status code: {response.status_code}"
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}")
            return f"Error: {str(e)}"
    
    def _format_size(self, size_bytes: int) -> str:
        """Format size in bytes to human-readable string
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted size string
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
    
    def get_gpu_info(self) -> Dict[str, Any]:
        """Get information about available GPUs for Ollama
        
        Returns:
            Dict with GPU availability and information
        """
        try:
            # Check GPU info using direct commands
            gpu_info = {"gpu_available": False}
            
            # Try nvidia-smi for NVIDIA GPUs
            try:
                nvidia_smi = subprocess.run(
                    ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,temperature.gpu", "--format=csv,noheader"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if nvidia_smi.returncode == 0 and nvidia_smi.stdout.strip():
                    gpu_info["nvidia_available"] = True
                    gpu_info["gpu_available"] = True
                    
                    # Parse the CSV output
                    nvidia_gpus = []
                    for line in nvidia_smi.stdout.strip().split('\n'):
                        if line.strip():
                            parts = [part.strip() for part in line.split(',')]
                            if len(parts) >= 4:
                                gpu_data = {
                                    "name": parts[0],
                                    "memory_total": parts[1],
                                    "memory_used": parts[2],
                                    "temperature": parts[3]
                                }
                                nvidia_gpus.append(gpu_data)
                    
                    gpu_info["nvidia_gpus"] = nvidia_gpus
                else:
                    gpu_info["nvidia_available"] = False
            except (FileNotFoundError, subprocess.SubprocessError):
                gpu_info["nvidia_available"] = False
            
            # Try rocm-smi for AMD GPUs
            try:
                rocm_smi = subprocess.run(
                    ["rocm-smi", "--showmeminfo", "vram"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if rocm_smi.returncode == 0 and rocm_smi.stdout.strip():
                    gpu_info["amd_available"] = True
                    gpu_info["gpu_available"] = True
                    
                    # Extract relevant info from rocm-smi output
                    amd_gpus = []
                    lines = rocm_smi.stdout.strip().split('\n')
                    # Basic parsing of rocm-smi output (could be improved with more detailed parsing)
                    for i, line in enumerate(lines):
                        if line.startswith('GPU') and 'VRAM' in line and i + 1 < len(lines):
                            # Extract device ID
                            device_id = line.split()[1].strip(':')
                            # Try to find name in a different command
                            try:
                                name_cmd = subprocess.run(
                                    ["rocm-smi", "-d", device_id, "--showname"],
                                    capture_output=True,
                                    text=True,
                                    timeout=2
                                )
                                name = "AMD GPU"
                                for name_line in name_cmd.stdout.strip().split('\n'):
                                    if 'GPU' in name_line and 'Name' in name_line:
                                        name = name_line.split(':')[-1].strip()
                                        break
                            except:
                                name = f"AMD GPU {device_id}"
                                
                            # Try to extract memory info
                            mem_line = lines[i + 1]
                            mem_total = "Unknown"
                            mem_used = "Unknown"
                            
                            if 'Total' in mem_line and 'Used' in mem_line:
                                parts = mem_line.split()
                                for j, part in enumerate(parts):
                                    if part == 'Total:' and j + 1 < len(parts):
                                        mem_total = parts[j + 1]
                                    if part == 'Used:' and j + 1 < len(parts):
                                        mem_used = parts[j + 1]
                            
                            amd_gpus.append({
                                "name": name,
                                "memory_total": mem_total,
                                "memory_used": mem_used,
                                "device_id": device_id
                            })
                    
                    gpu_info["amd_gpus"] = amd_gpus
                else:
                    gpu_info["amd_available"] = False
            except (FileNotFoundError, subprocess.SubprocessError):
                gpu_info["amd_available"] = False
            
            # If both nvidia and amd checks failed, get CPU info
            if not gpu_info.get("gpu_available"):
                # Get CPU info as fallback
                try:
                    cpu_info_cmd = subprocess.run(
                        ["cat", "/proc/cpuinfo"],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    
                    if cpu_info_cmd.returncode == 0:
                        # Parse CPU info
                        cpu_model = "Unknown CPU"
                        cpu_cores = 0
                        
                        for line in cpu_info_cmd.stdout.strip().split('\n'):
                            if line.startswith('model name'):
                                cpu_model = line.split(':', 1)[1].strip()
                            if line.startswith('processor'):
                                cpu_cores += 1
                        
                        gpu_info["cpu_info"] = {
                            "model": cpu_model,
                            "cores": cpu_cores
                        }
                except:
                    gpu_info["cpu_info"] = {"model": "Unknown CPU", "cores": "Unknown"}
            
            return gpu_info
            
        except Exception as e:
            logger.error(f"Error getting GPU info: {str(e)}")
            return {"error": str(e), "gpu_available": False} 