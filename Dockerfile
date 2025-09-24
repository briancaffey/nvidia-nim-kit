# Multi-stage Dockerfile for nvidia-nim-kit backend
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgl1 \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Set working directory
WORKDIR /app

# Copy dependency files first (for better caching)
COPY pyproject.toml LICENSE ./

# Install uv and create virtual environment
RUN pip install uv && \
    uv venv && \
    . .venv/bin/activate && \
    uv pip install -e . && \
    uv pip install -e ".[dev]"

# Copy source code (excluding media files via .dockerignore)
COPY --chown=app:app nimkit/ ./nimkit/

# Create directories for celery and media with proper permissions
# Do this after copying source code to ensure directories exist
RUN mkdir -p /app/celery-data /app/nimkit/media && \
    chown -R app:app /app/celery-data /app/nimkit/media

USER app

# Set PATH to include virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/health')" || exit 1

# Expose port
EXPOSE 8000

# Default command
CMD ["/app/.venv/bin/python", "-m", "uvicorn", "nimkit.src.main:app", "--host", "0.0.0.0", "--port", "8000"]
