# Architecture Overview

## System Architecture

The TTB Label Verifier is designed with a **fail-open architecture** that prioritizes availability and rapid recovery over completeness. The system can operate in degraded mode with reduced capabilities rather than failing completely.

## Fail-Open Architecture

### Design Philosophy

**Traditional approach (fail-closed):**
- Application won't start until all dependencies are available
- Long initialization times (15-20 minutes)
- Single point of failure (Ollama model download)
- Poor user experience during deployment

**Our approach (fail-open):**
- Application starts immediately with available backends
- Fast RTO: 2-3 minutes to operational
- Graceful degradation when Ollama unavailable
- Progressive enhancement as capabilities come online

### Operational Modes

#### 1. Degraded Mode
**When:** Ollama model not yet downloaded or unavailable  
**Capabilities:**
- ✅ Ollama OCR available (~10 seconds per image)
- ✅ All validation endpoints functional
- ✅ Batch processing works
- ❌ Higher accuracy AI analysis not available

**Health Status:**
```json
{
  "status": "degraded",
  "backends": {
    "ollama": {"available": false, "error": "Model 'llama3.2-vision' not found"}
  },
  "capabilities": {
    "ocr_backends": [],
    "degraded_mode": true
  }
}
```

#### 2. Full Capability Mode
**When:** All backends available  
**Capabilities:**
- ✅ Ollama OCR (high accuracy)
- ✅ Users can choose backend per request
- ✅ All features operational

**Health Status:**
```json
{
  "status": "healthy",
  "backends": {
    "ollama": {"available": true, "error": null}
  },
  "capabilities": {
    "ocr_backends": ["ollama"],
    "degraded_mode": false
  }
}
```

## Component Architecture

### API Layer (`app/api.py`)
- **FastAPI** web framework
- **Health endpoint** (`GET /health`) - Returns system status
- **Verify endpoint** (`POST /verify`) - Single label verification
- **Batch endpoint** (`POST /verify/batch`) - Multi-label verification
- **Error handling** - Returns 503 with Retry-After when Ollama requested but unavailable

### OCR Backends (`app/ocr_backends.py`)
- **Ollama Backend** - Lazy initialization, high accuracy (~10s), requires model download

### Validation Engine (`app/validators.py`)
- Brand name validation (fuzzy matching, 90% threshold)
- ABV validation (product-specific tolerances)
- Net contents validation (volume extraction)
- Government warning validation (exact format matching)
- Bottler information extraction

## Deployment Architecture

### EC2 Instance Initialization

**Timeline:**
```
T+0:00   Instance launched
T+0:30   Docker installed
T+1:00   Ollama container started
T+2:00   Verifier app deployed (DEGRADED MODE) ✅ Traffic served
T+2:01   Background model download begins
T+10:00  Model download completes
T+10:30  Ollama backend available (FULL CAPABILITY) ✅
```

**Key Features:**
1. **Non-blocking deployment** - App deploys immediately, doesn't wait for model
2. **Background download** - 6.7 GB model downloads in parallel with traffic serving
3. **Self-healing** - If model not in S3, downloads from Ollama and exports to S3
4. **Space-aware** - Uses `/home` instead of `/tmp` for large file downloads

### Infrastructure Components

- **Application Load Balancer** - HTTPS termination, health checks
- **EC2 t3.medium** - Docker host (2 vCPU, 4 GB RAM, 50 GB disk)
- **Docker Compose** - Container orchestration
- **S3** - Model artifact storage for fast recovery
- **SSM** - Remote access without SSH keys
- **ACM** - TLS certificate management

## Performance Characteristics

### Recovery Time Objective (RTO)

| Scenario | Old Design | New Design | Improvement |
|----------|-----------|-----------|-------------|
| Cold start (no S3 model) | 15-20 min | 2-3 min (degraded) | **87% faster** |
| Warm start (S3 model exists) | 8-10 min | 2-3 min (degraded) | **75% faster** |
| Full capability | 15-20 min | 10-12 min (full) | **40% faster** |

### Processing Performance

| Backend | Speed | Accuracy | Use Case |
|---------|-------|----------|----------|
| Ollama | ~10s | Excellent | High-accuracy requirements, edge cases |

## Monitoring & Observability

### Health Check Endpoint

**Endpoint:** `GET /health`  
**Purpose:** Single source of truth for system status  
**Used by:** ALB health checks, monitoring systems, operators

**Response Fields:**
- `status`: Overall system health (`healthy`, `degraded`)
- `backends`: Per-backend availability and errors
- `capabilities`: Available OCR backends and mode

### Logging

- **Application logs**: Docker container stdout/stderr
- **Model download logs**: `/var/log/ollama-model-download.log`
- **System logs**: CloudWatch via SSM agent (optional)

### Monitoring Recommendations

**Critical Metrics:**
- Health endpoint status (should be 200, may show `degraded`)
- Response time percentiles (p50, p95, p99)
- Error rates by endpoint
- Backend availability (Ollama should always be 100%)

**Alerts:**
- Ollama unavailable >1 hour (warning - prolonged degradation)
- Error rate >5% (warning)
- Response time p95 >10s (warning)

## Security Considerations

### Network Security
- **Public IP**: EC2 instance has public IP (required for Docker Hub, S3, SSM in default VPC)
- **Security Groups**: Only ALB can reach port 8000, no SSH access
- **HTTPS**: Enforced via ALB with ACM certificate
- **Future Enhancement**: Remove public IP by adding VPC endpoints + NAT Gateway (see `infrastructure/FUTURE_ENHANCEMENTS.md`)

### Access Control
- **SSM**: Remote access via AWS Systems Manager (no SSH keys)
- **OIDC**: GitHub Actions uses OIDC (no long-lived credentials)
- **IAM**: Least privilege roles for EC2 and GitHub Actions

### Data Security
- **TLS 1.2+**: Enforced on ALB
- **No PII**: Label images contain product info, not personal data
- **Audit Trail**: CloudTrail logs all API calls, ALB logs all requests



## Testing Strategy

### Test Levels
1. **Unit Tests** - Individual components (validators, parsers)
2. **Integration Tests** - API endpoints with mocked backends
3. **E2E Tests** - Full stack with real OCR backends
4. **Load Tests** - Performance and concurrency validation

## Future Enhancements

### Operational Improvements
1. **Model download progress endpoint** - Real-time visibility into background download
2. **Metrics endpoint** - Prometheus-compatible metrics
3. **Graceful shutdown** - Drain connections before termination

### Infrastructure Improvements
1. **Remove public IP** - Add VPC endpoints + NAT Gateway
2. **Multi-AZ deployment** - HA across availability zones
3. **Auto-scaling** - Scale based on request rate

### Feature Improvements
1. **Artifact storage** - Save request/response for debugging
2. **Webhooks** - Async notification when batch complete
3. **Rate limiting** - Protect against abuse

See `infrastructure/FUTURE_ENHANCEMENTS.md` for detailed enhancement proposals.

## Recommended Production Architecture

```
Internet
   ↓
CloudFront (WAF)
   ↓
AWS API Gateway
   ├── Authentication (API keys)
   ├── Rate limiting
   ├── Request throttling
   ├── CloudWatch metrics
   ↓
EKS Cluster
   ├── UI Node Pool
   ├── API Node Pool  
   ├── Ollama Node Pool
```

**Why API Gateway?**
- ✅ Handles authentication/authorization
- ✅ Built-in rate limiting
- ✅ Request validation
- ✅ CloudWatch integration
- ✅ Usage plans and quotas
- ✅ No code changes needed

## References

- [API Documentation](docs/API_README.md)
- [Deployment Guide](infrastructure/DEPLOYMENT_GUIDE.md)
- [Testing Guide](docs/TESTING_GUIDE.md)
- [Requirements](docs/REQUIREMENTS.md)
