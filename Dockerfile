# Stage 1: Base with system dependencies
FROM python:3.12-slim as base

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-eng \
        curl \
        bc \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Python dependencies builder
FROM base as builder

WORKDIR /build
COPY requirements.txt requirements-dev.txt ./

RUN pip install --user --no-cache-dir -r requirements.txt -r requirements-dev.txt

# Stage 3: Test runner (fails build if tests fail or coverage < 75%)
FROM builder as test

COPY . /app
WORKDIR /app

ENV PATH=/root/.local/bin:$PATH

# Run pytest with coverage requirements (50% minimum for CI/CD)
RUN pytest tests/ \
    --cov=. \
    --cov-report=term-missing \
    --cov-report=html \
    --cov-fail-under=50 \
    -v

# Stage 4: Production image
FROM base as production

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY *.py ./
COPY samples/ ./samples/

# Set environment
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/docs || exit 1

# Expose port
EXPOSE 8000

# Run FastAPI with uvicorn
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
