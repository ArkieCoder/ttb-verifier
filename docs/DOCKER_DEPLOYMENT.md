# Docker Deployment Guide - TTB Label Verifier

## Overview

This guide covers building, running, and deploying the TTB Label Verifier in Docker containers. The application uses a multi-stage Docker build with separate services for the main verifier and Ollama AI.

**Architecture:**
- Main verifier app (~500MB): Python 3.12 + Tesseract OCR + FastAPI
- Ollama service (~4GB): AI vision models for high-accuracy OCR
- Docker Compose orchestrates both services

---

## Prerequisites

### Required

- **Docker:** 24.0+ ([Install Docker](https://docs.docker.com/get-docker/))
- **Docker Compose:** 2.20+ ([Install Compose](https://docs.docker.com/compose/install/))
- **Disk Space:** ~5GB for images and models
- **RAM:** 8GB minimum, 16GB recommended

### Optional (For Ollama GPU Support)

- **NVIDIA GPU:** For faster Ollama processing
- **NVIDIA Container Toolkit:** ([Install Guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html))
- **CUDA Compatible GPU:** Check with `nvidia-smi`

---

## Quick Start

### 1. Clone Repository

```bash
git clone <repository-url>
cd takehome
```

### 2. Build Images

```bash
# Build all services
docker-compose build

# Or build specific service
docker build -t ttb-verifier:latest .
```

**Build Time:**
- First build: ~5-10 minutes (downloads base images, installs dependencies)
- Subsequent builds: ~1-2 minutes (uses cache)

**Note:** Build automatically runs tests. If tests fail or coverage <80%, build fails.

### 3. Start Services

```bash
# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### 4. Pull Ollama Model (First Time)

```bash
# Pull llama3.2-vision model (~7.9GB)
docker-compose exec ollama ollama pull llama3.2-vision

# Verify model downloaded
docker-compose exec ollama ollama list
```

**Download Time:** ~5-15 minutes depending on connection

### 5. Test API

```bash
# Check API is responding
curl http://localhost:8000/docs

# Test single label
curl -X POST http://localhost:8000/verify \
  -F "image=@samples/label_good_001.jpg" \
  -F "ocr_backend=tesseract"
```

### 6. Stop Services

```bash
# Stop containers
docker-compose down

# Stop and remove volumes (clears Ollama models)
docker-compose down -v
```

---

## Docker Multi-Stage Build

### Build Stages

The `Dockerfile` uses a 4-stage build process:

```
Stage 1: base
├── Python 3.12-slim
├── Tesseract OCR
├── System utilities (curl, bc)
└── ~200MB

Stage 2: builder
├── Install Python dependencies
├── pip packages in /root/.local
└── ~350MB

Stage 3: test
├── Copy application code
├── Run pytest with 80% coverage requirement
├── ⚠️ Build FAILS if tests fail
└── (Intermediate, not kept)

Stage 4: production
├── Copy Python packages from builder
├── Copy application code
├── Add health check
└── ~500MB final image
```

### Building Specific Stages

```bash
# Build only up to test stage (useful for debugging)
docker build --target test -t ttb-verifier:test .

# Build production stage (default)
docker build -t ttb-verifier:production .

# Build without cache (clean build)
docker build --no-cache -t ttb-verifier:latest .
```

---

## Docker Compose Configuration

### Services

#### Verifier Service

**Image:** Built from Dockerfile  
**Ports:** 8000 (API)  
**Environment Variables:**

```yaml
environment:
  - OLLAMA_HOST=http://ollama:11434
  - OLLAMA_MODEL=llama3.2-vision
  - LOG_LEVEL=INFO
  - MAX_FILE_SIZE_MB=10
  - MAX_BATCH_SIZE=50
  - DEFAULT_OCR_BACKEND=tesseract
  - CORS_ORIGINS=["*"]
```

**Health Check:**
- Interval: 30s
- Timeout: 3s
- Retries: 3
- Start period: 10s

**Depends On:** ollama (waits for ollama health check to pass)

#### Ollama Service

**Image:** ollama/ollama:latest  
**Ports:** 11434 (Ollama API)  
**Volumes:** ollama_models (persists downloaded models)

**GPU Support:**
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```

**Health Check:**
- Command: `ollama list`
- Interval: 10s
- Timeout: 5s
- Retries: 5
- Start period: 30s

### Networks

**ttb-network (bridge):** Allows services to communicate by service name

### Volumes

**ollama_models:** Persists Ollama models across restarts (survives `docker-compose down`)

---

## Configuration

### Environment Variables

Create `.env` file in project root:

```bash
# Copy example
cp .env.example .env

# Edit configuration
vim .env
```

**Example `.env`:**
```bash
# Ollama Configuration
OLLAMA_HOST=http://ollama:11434
OLLAMA_MODEL=llama3.2-vision

# App Configuration
LOG_LEVEL=INFO
MAX_FILE_SIZE_MB=10
MAX_BATCH_SIZE=50
DEFAULT_OCR_BACKEND=tesseract

# CORS Configuration
CORS_ORIGINS=["*"]

# Future: S3 Configuration
# S3_BUCKET=my-ttb-samples
# S3_REGION=us-east-1
```

### Customizing docker-compose.yml

**Override for Development:**

Create `docker-compose.override.yml`:
```yaml
version: '3.8'

services:
  verifier:
    volumes:
      # Mount code for live reload (development only)
      - ./:/app
    environment:
      - LOG_LEVEL=DEBUG
  
  ollama:
    # Disable GPU for development
    deploy: {}
```

**Production Configuration:**

```yaml
version: '3.8'

services:
  verifier:
    restart: always
    environment:
      - LOG_LEVEL=WARNING
      - CORS_ORIGINS=["https://ttb.gov"]
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

## Ollama Setup

### GPU vs CPU

#### With NVIDIA GPU (Recommended)

**Requirements:**
- NVIDIA GPU with CUDA support
- NVIDIA Container Toolkit installed

**Check GPU:**
```bash
# On host
nvidia-smi

# In Ollama container
docker-compose exec ollama nvidia-smi
```

**Performance:**
- ~20-30s per label with llama3.2-vision
- Much faster than CPU

#### Without GPU (CPU Only)

**Modify docker-compose.yml:**
```yaml
ollama:
  # Remove or comment out GPU configuration
  # deploy:
  #   resources:
  #     reservations:
  #       devices:
  #         - driver: nvidia
```

**Performance:**
- ~60-90s per label with llama3.2-vision
- Significantly slower but still works

### Managing Models

```bash
# List downloaded models
docker-compose exec ollama ollama list

# Pull specific model
docker-compose exec ollama ollama pull llama3.2-vision

# Remove model (free up space)
docker-compose exec ollama ollama rm llama3.2-vision

# Show model info
docker-compose exec ollama ollama show llama3.2-vision
```

### Model Storage

Models stored in Docker volume: `ollama_models`

**Check volume size:**
```bash
docker volume ls
docker volume inspect takehome_ollama_models
```

**Backup models:**
```bash
# Export volume
docker run --rm -v takehome_ollama_models:/data -v $(pwd):/backup \
  alpine tar czf /backup/ollama_models_backup.tar.gz -C /data .

# Restore volume
docker run --rm -v takehome_ollama_models:/data -v $(pwd):/backup \
  alpine tar xzf /backup/ollama_models_backup.tar.gz -C /data
```

---

## Running Without Ollama (Tesseract Only)

For faster builds and reduced resource usage, run without Ollama:

### Option 1: Modify docker-compose.yml

```yaml
services:
  verifier:
    environment:
      - DEFAULT_OCR_BACKEND=tesseract
    # Remove depends_on ollama
  
  # Comment out entire ollama service
  # ollama:
  #   ...
```

### Option 2: Override File

Create `docker-compose.tesseract.yml`:
```yaml
version: '3.8'

services:
  verifier:
    environment:
      - OLLAMA_HOST=http://localhost:11434  # Won't be used
      - DEFAULT_OCR_BACKEND=tesseract
```

Run with:
```bash
docker-compose -f docker-compose.yml -f docker-compose.tesseract.yml up -d
```

**Result:**
- Image size: ~500MB (vs ~4.5GB with Ollama)
- Faster startup: <10s
- Processing: 0.7s per label
- Lower accuracy with decorative fonts

---

## Testing in Docker

### Running Tests During Build

Tests run automatically during `docker build`:

```bash
# Build and run tests
docker build -t ttb-verifier:test .

# If tests fail, build fails
# Check logs for test output
```

### Running Tests in Container

```bash
# Run tests in existing container
docker-compose exec verifier pytest tests/ -v

# With coverage report
docker-compose exec verifier pytest tests/ --cov=. --cov-report=html

# Run specific test file
docker-compose exec verifier pytest tests/test_unit/test_field_validators.py -v

# Run only unit tests
docker-compose exec verifier pytest tests/test_unit/ -v
```

### Extracting Coverage Report

```bash
# Generate coverage HTML report
docker-compose exec verifier pytest tests/ --cov=. --cov-report=html

# Copy report from container
docker cp $(docker-compose ps -q verifier):/app/htmlcov ./coverage_report

# Open in browser
open coverage_report/index.html
```

---

## Logging

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f verifier
docker-compose logs -f ollama

# Last 100 lines
docker-compose logs --tail=100 verifier

# Since timestamp
docker-compose logs --since 2026-02-16T10:00:00 verifier
```

### Log Configuration

**Default:** Logs to stdout (captured by Docker)

**Log Format:**
```
2026-02-16 12:00:00 - uvicorn.access - INFO - POST /verify 200
2026-02-16 12:00:01 - app - INFO - Processed label_001.jpg in 0.72s
```

**Production Logging:**

Forward logs to external service (Splunk, CloudWatch, etc.):

```yaml
services:
  verifier:
    logging:
      driver: "syslog"
      options:
        syslog-address: "tcp://logs.example.com:514"
```

Or use log aggregator:
```bash
# Send to CloudWatch
docker-compose logs verifier | aws logs put-log-events ...
```

---

## Health Checks

### Container Health

```bash
# Check health status
docker-compose ps

# View health check logs
docker inspect $(docker-compose ps -q verifier) | jq '.[0].State.Health'
```

### Manual Health Check

```bash
# Verifier health (when implemented)
curl http://localhost:8000/health

# Ollama health
docker-compose exec ollama ollama list
```

---

## Performance Optimization

### Image Size Optimization

**Current:** ~500MB production image

**Further Optimization:**
```dockerfile
# Use alpine base (smaller but more compatibility issues)
FROM python:3.12-alpine as base

# Or use distroless (no shell, most secure)
FROM gcr.io/distroless/python3:latest
```

**Not recommended unless disk space critical:**
- Alpine requires compiling many Python packages (slower builds)
- Distroless removes debugging tools

### Build Cache

**Speed up builds:**
```bash
# Use BuildKit (faster, better caching)
DOCKER_BUILDKIT=1 docker build -t ttb-verifier:latest .

# Parallel builds with compose
COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker-compose build --parallel
```

### Resource Limits

**Prevent containers from consuming all resources:**

```yaml
services:
  verifier:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
  
  ollama:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 16G
```

---

## Deployment Scenarios

### Local Development

```bash
# Start services
docker-compose up -d

# Develop and test
# Edit code, rebuild only if Dockerfile changes
docker-compose up -d --build verifier

# Stop when done
docker-compose down
```

### Single EC2 Instance

```bash
# SSH to EC2
ssh -i key.pem ubuntu@ec2-instance

# Install Docker & Docker Compose
sudo apt-get update
sudo apt-get install -y docker.io docker-compose

# Clone repository
git clone <repo-url>
cd takehome

# Create .env with production config
cat > .env <<EOF
LOG_LEVEL=WARNING
CORS_ORIGINS=["https://ttb.gov"]
EOF

# Start services
sudo docker-compose up -d

# Check logs
sudo docker-compose logs -f

# Enable restart on boot
sudo docker update --restart=always $(sudo docker ps -q)
```

### Multiple Instances (Load Balanced)

**Architecture:**
```
ALB (Application Load Balancer)
├── EC2 Instance 1 (verifier + ollama)
├── EC2 Instance 2 (verifier + ollama)
└── EC2 Instance 3 (verifier + ollama)
```

**Considerations:**
- Each instance runs both verifier and ollama
- ALB distributes requests across instances
- Ollama models duplicated on each instance (~8GB per instance)
- Can share Ollama service across instances (more complex networking)

### Container Orchestration (ECS/Kubernetes)

**Future Consideration:** For high availability and auto-scaling

**ECS Task Definition:**
```json
{
  "containerDefinitions": [
    {
      "name": "verifier",
      "image": "gcr.io/project/ttb-verifier:latest",
      "portMappings": [{"containerPort": 8000}],
      "environment": [
        {"name": "OLLAMA_HOST", "value": "http://ollama:11434"}
      ]
    },
    {
      "name": "ollama",
      "image": "ollama/ollama:latest",
      "portMappings": [{"containerPort": 11434}]
    }
  ]
}
```

---

## Troubleshooting

### Build Fails at Test Stage

**Symptom:** `docker build` fails with pytest errors

**Solution:**
```bash
# Run tests locally first
pytest tests/ -v

# Check which tests are failing
pytest tests/ -x  # Stop at first failure

# Fix tests, then rebuild
docker build --no-cache -t ttb-verifier:latest .
```

### Ollama Container Won't Start

**Symptom:** `docker-compose up` shows ollama unhealthy

**Diagnostics:**
```bash
# Check Ollama logs
docker-compose logs ollama

# Check if container running
docker-compose ps ollama

# Try starting Ollama manually
docker-compose up ollama
```

**Common Causes:**
- GPU not available (remove GPU config if no NVIDIA GPU)
- Insufficient disk space (check `df -h`)
- Port 11434 already in use (check `netstat -tulpn | grep 11434`)

### Verifier Container Crashes

**Symptom:** Container exits immediately after starting

**Diagnostics:**
```bash
# View exit logs
docker-compose logs verifier

# Run container interactively
docker-compose run --rm verifier /bin/bash

# Check if Python dependencies installed
docker-compose run --rm verifier python -c "import fastapi; print(fastapi.__version__)"
```

### Cannot Connect to API

**Symptom:** `curl http://localhost:8000` fails

**Diagnostics:**
```bash
# Check if container running
docker-compose ps

# Check port mapping
docker port $(docker-compose ps -q verifier)

# Check logs for errors
docker-compose logs verifier

# Check from inside container
docker-compose exec verifier curl localhost:8000/docs
```

### High Memory Usage

**Symptom:** System runs out of memory

**Cause:** Ollama models load into RAM (~8GB)

**Solutions:**
```bash
# Limit Ollama memory
docker-compose stop
# Edit docker-compose.yml with memory limits
docker-compose up -d

# Or use smaller model
docker-compose exec ollama ollama pull llama3.2:latest  # Smaller, text-only
```

### Slow Processing

**Symptom:** Requests timeout or take minutes

**Causes & Solutions:**

**Using Ollama on CPU:**
- Expected: 60-90s per label
- Solution: Use GPU or switch to Tesseract

**Ollama not responding:**
```bash
# Check Ollama status
docker-compose exec ollama ollama list

# Restart Ollama
docker-compose restart ollama
```

**Container resource constrained:**
```bash
# Check resource usage
docker stats

# Remove resource limits in docker-compose.yml
```

---

## Maintenance

### Updating Images

```bash
# Pull latest base images
docker pull python:3.12-slim
docker pull ollama/ollama:latest

# Rebuild
docker-compose build --no-cache

# Restart services
docker-compose up -d
```

### Cleaning Up

```bash
# Remove stopped containers
docker-compose down

# Remove volumes (clears Ollama models)
docker-compose down -v

# Remove all unused Docker objects
docker system prune -a

# Clean up build cache
docker builder prune
```

### Backing Up

**Backup Ollama models:**
```bash
docker volume ls  # Find volume name
docker run --rm -v takehome_ollama_models:/data -v $(pwd):/backup \
  alpine tar czf /backup/ollama_models.tar.gz -C /data .
```

**Backup configuration:**
```bash
tar czf ttb-config-backup.tar.gz .env docker-compose.yml
```

---

## Security Considerations

### Current State (Prototype)

- ⚠️ No authentication
- ⚠️ CORS allows all origins
- ⚠️ No rate limiting
- ⚠️ Running as root in container

**Acceptable for:**
- Development
- Internal testing
- Proof of concept

### Production Hardening

**1. Run as non-root:**
```dockerfile
RUN useradd -m -u 1000 appuser
USER appuser
```

**2. Read-only filesystem:**
```yaml
services:
  verifier:
    read_only: true
    tmpfs:
      - /tmp
```

**3. Network segmentation:**
```yaml
networks:
  frontend:
    internal: false
  backend:
    internal: true

services:
  verifier:
    networks:
      - frontend
      - backend
  ollama:
    networks:
      - backend
```

**4. Use secrets for sensitive config:**
```yaml
secrets:
  api_key:
    file: ./secrets/api_key.txt

services:
  verifier:
    secrets:
      - api_key
```

**5. Scan images for vulnerabilities:**
```bash
docker scan ttb-verifier:latest
trivy image ttb-verifier:latest
```

---

## Integration with CI/CD

### GitHub Actions (Future)

**Workflow File:** `.github/workflows/build-and-push.yml`

```yaml
name: Build and Push

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build and test
        run: docker build --target test .
  
  push:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Build production
        run: docker build -t gcr.io/${{ secrets.GCP_PROJECT }}/ttb-verifier:${{ github.sha }} .
      
      - name: Push to GCR
        run: docker push gcr.io/${{ secrets.GCP_PROJECT }}/ttb-verifier:${{ github.sha }}
```

### Deploying from GCR to EC2

```bash
# On EC2 instance

# Authenticate to GCR
gcloud auth configure-docker gcr.io

# Pull image
docker pull gcr.io/project-id/ttb-verifier:latest

# Update docker-compose.yml
services:
  verifier:
    image: gcr.io/project-id/ttb-verifier:latest

# Deploy
docker-compose up -d
```

---

## Resources

- **Docker Documentation:** https://docs.docker.com/
- **Docker Compose:** https://docs.docker.com/compose/
- **Ollama Docker:** https://hub.docker.com/r/ollama/ollama
- **FastAPI in Docker:** https://fastapi.tiangolo.com/deployment/docker/

---

## Support

For issues or questions:
- Check troubleshooting section above
- Review container logs: `docker-compose logs`
- Run tests: `docker-compose exec verifier pytest tests/ -v`
- GitHub Issues: (Add repository URL)

---

**Last Updated:** 2026-02-16  
**Docker Version Tested:** 24.0.7  
**Docker Compose Version Tested:** 2.20.0
