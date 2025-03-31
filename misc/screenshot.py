import os
import time
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def check_docker_running():
    """Check if Docker is running"""
    try:
        subprocess.run(["docker", "info"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("Docker is running.")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: Docker is not running or not installed.")
        return False

def build_and_run_docker():
    """Build and run the AIONE Docker container"""
    # Check if container is already running
    result = subprocess.run(
        ["docker", "ps", "-q", "-f", "name=aione"], 
        capture_output=True, 
        text=True
    )
    
    if result.stdout.strip():
        print("AIONE container is already running.")
        return True
    
    # Check if container exists but is stopped
    result = subprocess.run(
        ["docker", "ps", "-a", "-q", "-f", "name=aione"], 
        capture_output=True, 
        text=True
    )
    
    if result.stdout.strip():
        print("Starting existing AIONE container...")
        subprocess.run(["docker", "start", "aione"], check=True)
        return True
    
    # Build and run new container
    print("Building AIONE Docker image...")
    build_process = subprocess.run(
        ["docker", "build", "-t", "aione:latest", "../baseimage"], 
        check=True
    )
    
    if build_process.returncode != 0:
        print("Error building Docker image.")
        return False
    
    print("Running AIONE Docker container...")
    # Check if GPU is available and use it if possible
    gpu_flag = []
    try:
        gpu_check = subprocess.run(["nvidia-smi"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if gpu_check.returncode == 0:
            gpu_flag = ["--gpus", "all"]
            print("NVIDIA GPU detected, enabling GPU acceleration.")
    except FileNotFoundError:
        print("No NVIDIA GPU detected, running in CPU-only mode.")
    
    run_process = subprocess.run(
        ["docker", "run", "-d", "--name", "aione"] + 
        gpu_flag + 
        ["-p", "11434:11434", "-p", "5433:5433", "-p", "8081:8081", "-p", "7071:7071", "aione:latest"], 
        check=True
    )
    
    if run_process.returncode != 0:
        print("Error running Docker container.")
        return False
    
    print("AIONE container is now running.")
    # Wait for services to initialize
    print("Waiting for services to initialize (30 seconds)...")
    time.sleep(30)
    return True

def take_screenshots():
    """Access the web interface and take screenshots of each tab"""
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--headless")  # Run in headless mode
    
    # Initialize the WebDriver
    print("Initializing Chrome WebDriver...")
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Navigate to the web interface
        print("Accessing web interface at http://localhost:7071...")
        driver.get("http://localhost:7071")
        
        # Wait for page to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "models-tab"))
        )
        
        # Create screenshots directory if it doesn't exist
        os.makedirs("images", exist_ok=True)
        
        # Take screenshot of Models Tab (default tab)
        print("Taking screenshot of Models Tab...")
        driver.save_screenshot("images/models_tab.png")
        
        # Switch to Terminal Tab and take screenshot
        print("Taking screenshot of Terminal Tab...")
        terminal_tab = driver.find_element(By.ID, "terminal-tab")
        terminal_tab.click()
        time.sleep(2)  # Wait for tab content to load
        driver.save_screenshot("images/terminal_tab.png")
        
        # Switch to Chat Tab and take screenshot
        print("Taking screenshot of Chat Tab...")
        chat_tab = driver.find_element(By.ID, "chat-tab")
        chat_tab.click()
        time.sleep(2)  # Wait for tab content to load
        driver.save_screenshot("images/chat_tab.png")
        
        print("Screenshots taken successfully and saved to the 'images' directory.")
    except Exception as e:
        print(f"Error taking screenshots: {e}")
    finally:
        driver.quit()

def main():
    """Main function to run the script"""
    if not check_docker_running():
        return
    
    if build_and_run_docker():
        # Wait a bit more to ensure the web interface is fully loaded
        print("Waiting for web interface to be fully loaded...")
        time.sleep(10)
        take_screenshots()
        print("All tasks completed successfully.")
        print("Screenshots saved in the 'images' directory.")

if __name__ == "__main__":
    main() 