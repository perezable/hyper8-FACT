#!/bin/bash
# Entrypoint script for Railway deployment
# This script clears proxy environment variables before starting the application

echo "Starting FACT System on Railway..."
echo "Clearing proxy environment variables..."

# Clear all proxy-related environment variables
unset HTTP_PROXY
unset HTTPS_PROXY
unset http_proxy
unset https_proxy
unset ALL_PROXY
unset all_proxy
unset NO_PROXY
unset no_proxy
unset REQUESTS_CA_BUNDLE
unset CURL_CA_BUNDLE

# Export empty proxy variables to ensure they're cleared
export HTTP_PROXY=""
export HTTPS_PROXY=""
export http_proxy=""
export https_proxy=""
export NO_PROXY="*"
export no_proxy="*"

echo "Proxy variables cleared"
echo "Starting Python application..."

# Run the main application
exec python main.py