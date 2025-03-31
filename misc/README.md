# AIONE Screenshot Script

This script automates the process of:
1. Building and running the AIONE Docker container
2. Accessing the web interface at http://localhost:7071
3. Taking screenshots of each tab (Models, Terminal, Chat)

## Prerequisites

- Python 3.6+
- Docker installed and running
- Chrome or Chromium browser installed

## Installation

1. Install the required Python packages:
```
pip install -r requirements.txt
```

## Usage

1. Simply run the script:
```
python screenshot.py
```

The script will:
- Check if Docker is running
- Build the AIONE Docker image if it doesn't exist
- Start the AIONE container
- Wait for services to initialize
- Take screenshots of each tab (Models, Terminal, Chat)
- Save the screenshots to the `images` directory

## Output

The script generates the following screenshots in the `images` directory:
- `models_tab.png`: Screenshot of the Models tab
- `terminal_tab.png`: Screenshot of the Terminal tab
- `chat_tab.png`: Screenshot of the Chat tab

These images match the ones shown in the AIONE README.md file. 