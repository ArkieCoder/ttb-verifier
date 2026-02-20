# Stage 1: Base with system dependencies
FROM python:3.12-slim AS base

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        bc \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Python dependencies builder
FROM base AS builder

WORKDIR /build
COPY app/requirements.txt app/requirements-dev.txt ./

RUN pip install --user --no-cache-dir -r requirements.txt -r requirements-dev.txt

# Stage 3: Test runner (fails build if tests fail or coverage < 50%)
FROM builder AS test

COPY app/ /app
COPY samples/ /app/samples
WORKDIR /app

ENV PATH=/root/.local/bin:$PATH

# Run pytest with coverage requirements (50% minimum for CI/CD)
RUN pytest tests/ \
    --cov=. \
    --cov-report=term-missing \
    --cov-report=html \
    --cov-fail-under=50 \
    -v

# Stage 4: Production image (FastAPI app — uvicorn 4 workers)
FROM base AS production

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY app/*.py ./

# Copy templates directory for UI
COPY app/templates ./templates

# Create samples directory (optional - for golden samples)
RUN mkdir -p ./samples

# Create jobs directory for async batch processing and queue DB
RUN mkdir -p /app/tmp/jobs /app/tmp/async

# Set environment
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/docs || exit 1

# Expose port
EXPOSE 8000

# Run FastAPI with uvicorn (4 workers for concurrent request handling)
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# Stage 5: Worker image (single-process queue consumer)
FROM base AS worker

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code (worker only needs queue_manager, worker, label_validator, ocr_backends)
COPY app/*.py ./

# Create shared volume directories
RUN mkdir -p /app/tmp/jobs /app/tmp/async

# Set environment
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# No health check port — worker has no HTTP server.
# Docker will mark it healthy if the process is running.
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "from queue_manager import QueueManager; QueueManager().queue_depth()" || exit 1

CMD ["python", "worker.py"]
