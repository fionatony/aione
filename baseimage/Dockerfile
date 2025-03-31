FROM ollama/ollama:latest

# Set labels for the image
LABEL maintainer="fionatony@gmail.com"
LABEL description="AIONE - AI service based on Ollama , Weaviate, Postgresql"
LABEL version="0.1.0"

# Set environment variables for non-interactive installation
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=America/New_York

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    procps \
    postgresql \
    postgresql-contrib \
    sudo \
    locales \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Create log directory
RUN mkdir -p /var/log && touch /var/log/webapp.log && chmod 666 /var/log/webapp.log

# Generate locales for UTF-8
RUN locale-gen en_US.UTF-8 && \
    update-locale LANG=en_US.UTF-8

# Create service directories
RUN mkdir -p /service/postgresql /service/weaviate/data

# Install Weaviate v1.28.11
RUN curl -L https://github.com/weaviate/weaviate/releases/download/v1.28.11/weaviate-v1.28.11-Linux-amd64.tar.gz -o /tmp/weaviate.tar.gz && \
    tar -xzf /tmp/weaviate.tar.gz -C /usr/local/bin && \
    rm /tmp/weaviate.tar.gz && \
    chmod +x /usr/local/bin/weaviate && \
    ln -s /usr/local/bin/weaviate /usr/bin/weaviate

# Set Weaviate environment variables
ENV AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED="true"
ENV PERSISTENCE_DATA_PATH="/service/weaviate/data"
ENV ENABLE_MODULES="text2vec-ollama,text2vec-huggingface,text2vec-openai"

# Expose the default Ollama port
EXPOSE 11434

# Expose PostgreSQL port (changed to 5433)
EXPOSE 5433

# Expose Weaviate port (changed to 8081)
EXPOSE 8081

# Expose web application port (changed to 7071)
EXPOSE 7071

# Set working directory
WORKDIR /app

# Copy web application files
COPY web /app/web
RUN pip3 install -r /app/web/requirements.txt

# Ensure proper permissions for static files
RUN chmod -R 755 /app/web/static

# Copy startup script
COPY start.sh /app/
RUN chmod +x /app/start.sh

# Use our custom startup script
ENTRYPOINT ["/app/start.sh"] 