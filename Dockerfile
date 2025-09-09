# Railway-optimized Dockerfile for FACT System
# Single-stage build optimized for Railway deployment

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # Disable any proxy environment variables that might interfere
    HTTP_PROXY="" \
    HTTPS_PROXY="" \
    http_proxy="" \
    https_proxy="" \
    NO_PROXY="*" \
    no_proxy="*" \
    # Enable Python to see Railway environment variables
    PYTHONPATH=/app \
    # Log level for debugging
    LOG_LEVEL=DEBUG

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements files
COPY requirements.txt requirements-security.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-security.txt

# Copy the entire application
COPY . .

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/output

# Set proper permissions
RUN chmod -R 755 /app

# Railway uses PORT environment variable
ENV PORT=8000
EXPOSE 8000

# Health check (Railway supports this)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Copy wrapper script
COPY railway_wrapper.py /app/railway_wrapper.py
RUN chmod +x /app/railway_wrapper.py

# Run the application via Railway wrapper to prevent proxy injection
CMD ["python", "railway_wrapper.py"]