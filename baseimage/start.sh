#!/bin/bash
set -e

echo "Starting AIONE services..."

# Function to check if a process is running
check_process() {
    pgrep -f "$1" >/dev/null
    return $?
}

# Function to start Ollama
start_ollama() {
    echo "Starting Ollama service..."
    
    # Start Ollama in the background
    ollama serve &
    
    # Wait for Ollama to be ready
    echo "Waiting for Ollama to be ready..."
    while ! curl -s "http://127.0.0.1:11434/api/version" > /dev/null 2>&1; do
        sleep 1
    done
    
    echo "Ollama is running!"
}

# Function to start PostgreSQL
start_postgresql() {
    echo "Starting PostgreSQL service..."
    
    # Initialize PostgreSQL if needed
    if [ ! -f "/service/postgresql/initialized" ]; then
        echo "Initializing PostgreSQL database..."
        
        # Initialize the database
        mkdir -p /service/postgresql/data
        chown -R postgres:postgres /service/postgresql
        
        # Set locale environment variables
        export LANG=en_US.UTF-8
        export LC_ALL=en_US.UTF-8
        
        # Initialize the PostgreSQL data directory with UTF-8 encoding
        sudo -u postgres /usr/lib/postgresql/*/bin/initdb -D /service/postgresql/data --encoding=UTF8 --lc-collate=en_US.UTF-8 --lc-ctype=en_US.UTF-8
        
        # Configure PostgreSQL to listen on all addresses and use port 5433
        echo "listen_addresses = '*'" >> /service/postgresql/data/postgresql.conf
        echo "port = 5433" >> /service/postgresql/data/postgresql.conf
        echo "host all all 0.0.0.0/0 trust" >> /service/postgresql/data/pg_hba.conf
        
        # Start PostgreSQL temporarily to verify encoding
        sudo -u postgres /usr/lib/postgresql/*/bin/pg_ctl -D /service/postgresql/data start
        sleep 2
        
        # Verify the encoding (case-insensitive comparison)
        ENCODING=$(sudo -u postgres psql -p 5433 -t -c "SHOW client_encoding;" | tr -d '[:space:]')
        if [ "${ENCODING,,}" != "utf8" ]; then
            echo "Warning: PostgreSQL client encoding is not UTF8 (got: $ENCODING)"
        fi
        
        # Stop PostgreSQL before continuing
        sudo -u postgres /usr/lib/postgresql/*/bin/pg_ctl -D /service/postgresql/data stop
        sleep 2
        
        # Create a file to indicate we've initialized
        touch /service/postgresql/initialized
    fi
    
    # Start PostgreSQL server
    sudo -u postgres /usr/lib/postgresql/*/bin/pg_ctl -D /service/postgresql/data start
    
    # Wait for PostgreSQL to be ready
    echo "Waiting for PostgreSQL to be ready..."
    while ! sudo -u postgres pg_isready -p 5433 -q; do
        sleep 1
    done
    
    # Verify encoding one final time (case-insensitive comparison)
    ENCODING=$(sudo -u postgres psql -p 5433 -t -c "SHOW client_encoding;" | tr -d '[:space:]')
    echo "PostgreSQL is running with encoding: $ENCODING"
}

# Function to start Weaviate
start_weaviate() {
    echo "Starting Weaviate service..."
    
    # Start Weaviate in the background
    # Environment variables from Dockerfile will be used for configuration
    weaviate --host 0.0.0.0 --port 8081 --scheme http &
    
    # Wait for Weaviate to be ready
    echo "Waiting for Weaviate to be ready..."
    while ! curl -s "http://127.0.0.1:8081/v1/.well-known/ready" > /dev/null 2>&1; do
        sleep 1
    done
    
    echo "Weaviate is running!"
}

# Function to start web application
start_web() {
    echo "Starting web application..."
    
    # Set the working directory to the web app directory
    cd /app/web
    
    # Set Flask environment variables
    export FLASK_APP=app.py
    export FLASK_ENV=production
    export APP_PORT=7071
    export OLLAMA_HOST="localhost"  # Since ollama is running on the same container
    export OLLAMA_PORT=11434
    export PYTHONUNBUFFERED=1  # Ensure Python output is not buffered
    
    # Start Flask application directly with error handling
    python3 -m flask run --host=0.0.0.0 --port=7071 >>/var/log/webapp.log 2>&1 &
    WEB_PID=$!
    
    echo "Web app started with PID: $WEB_PID"
    
    # Wait for web application to be ready
    echo "Waiting for web application to be ready..."
    max_attempts=30
    attempt=0
    while ! curl -s "http://127.0.0.1:7071/health" > /dev/null 2>&1; do
        attempt=$((attempt+1))
        if [ $attempt -ge $max_attempts ]; then
            echo "Web application failed to start after $max_attempts attempts"
            echo "Checking for errors in logs..."
            tail -n 50 /var/log/webapp.log
            if ! ps -p $WEB_PID > /dev/null; then
                echo "Web application process is not running!"
            fi
            break
        fi
        echo "Attempt $attempt/$max_attempts: Web app not ready yet, waiting..."
        sleep 2
    done
    
    if curl -s "http://127.0.0.1:7071/health" > /dev/null 2>&1; then
        echo "Web application is running!"
    else
        echo "Web application failed to start - continuing without it"
    fi
}

# Main execution
echo "Initializing services..."

# Start PostgreSQL
start_postgresql

# Start Ollama
start_ollama

# Start Weaviate
start_weaviate

# Start web application
start_web

echo "All services started successfully!"
echo "Available services:"
echo "- Ollama API: http://localhost:11434"
echo "- PostgreSQL: localhost:5433"
echo "- Weaviate: http://localhost:8081"
echo "- Web Interface: http://localhost:7071"

# Keep the script running to prevent container exit
echo "Services are running. Press Ctrl+C to stop."
tail -f /dev/null 