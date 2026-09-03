# Multi-stage lightweight Python 3.10 deployment image for Render
FROM python:3.10-slim

# Set environment variables for non-interactive and unbuffered execution
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    HOST=0.0.0.0 \
    ENVIRONMENT=production

# Install minimal OS dependencies needed for network/build
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .

# Install CPU-optimized PyTorch and application dependencies
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.4.1+cpu && \
    pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

# Copy application source and packaged data
COPY app/ ./app/

# Expose default backend port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/api/v1/health || exit 1

# Production startup command using shell format to interpolate $PORT
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
