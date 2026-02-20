# Development History

## Project Overview

**Goal:** Build an AI-powered alcohol beverage label verification system for the U.S. Treasury Department's Alcohol and Tobacco Tax and Trade Bureau (TTB) that validates label compliance with 27 CFR regulations.

**Timeline:** Initial development completed February 2026

**Key Deliverables:**
- REST API for label verification (FastAPI)
- Async queue-based verification (single image and batch)
- Retry endpoint for failed jobs
- Ollama (llama3.2-vision) as sole OCR backend
- Batch processing capability (up to 50 labels, async)
- Production-ready AWS infrastructure
- Fail-open architecture for high availability

## Requirements Summary

### Functional Requirements
1. **OCR Extraction:** Extract text from label images using Ollama (llama3.2-vision)
2. **Field Validation:** Verify required fields (brand name, ABV, net contents, bottler, government warning)
3. **Fuzzy Matching:** Handle OCR errors with 90% similarity threshold
4. **Product-Specific Rules:** Different ABV tolerances by product type
5. **Batch Processing:** Handle multiple labels via async queue
6. **Async Verify:** Single-image verification via queue (CloudFront-safe, pollable)
7. **Retry Endpoint:** Re-enqueue failed jobs without re-uploading

### Non-Functional Requirements
1. **Performance:** < 3s per label (Tesseract), acceptable degradation for Ollama
2. **Availability:** 99% uptime, graceful degradation when components unavailable
3. **Scalability:** Handle concurrent requests
4. **Maintainability:** Clear code structure, comprehensive tests
5. **Security:** HTTPS, no SSH access, IAM-based auth

### Success Criteria
- ✅ Ollama OCR backend functional
- ✅ Async queue (single-image and batch) operational
- ✅ Retry endpoint implemented
- ✅ API documented and tested
- ✅ Infrastructure automated (Terraform/Terragrunt)
- ✅ Test coverage > 50% (achieved 55%)
- ✅ Production deployment successful
- ✅ RTO < 5 minutes (achieved 2-3 minutes)

## Key Architectural Decisions

### 1. Fail-Open Architecture (High Impact)

**Problem:** Initial design blocked application startup on Ollama model download (6.7 GB), resulting in 15-20 minute RTO. Model download failed when using `/tmp` (tmpfs with only 1.9 GB capacity).

**Decision:** Implement fail-open architecture with graceful degradation:
- Application starts immediately with Tesseract backend
- Ollama model downloads in background (non-blocking)
- Health endpoint reports system status
- Returns 503 when Ollama requested but unavailable

**Alternatives Considered:**
- A) Fail-closed: Wait for all backends (rejected - poor RTO)
- B) Remove Ollama entirely (rejected - loss of accuracy option)
- C) Pre-bake model into AMI (rejected - complex pipeline)

**Result:** RTO improved from 15-20 minutes to 2-3 minutes (87% improvement)

### 2. Ollama-Only OCR

**Decision:** Use Ollama (llama3.2-vision) as the sole OCR backend

**Rationale:**
- Tesseract was evaluated but rejected: ~60-70% field accuracy with OCR errors on decorative fonts (e.g., "Black Brewing" → "Black ibealtl se")
- Ollama achieves ~95%+ accuracy
- The async queue architecture makes the ~58s Ollama latency acceptable — clients poll for results rather than waiting synchronously

**Tradeoffs:**
- Higher per-job latency (58s) vs Tesseract (~1s)
- Offset by queue-based async model and GPU acceleration on g4dn.2xlarge

### 3. Infrastructure: Default VPC with Public IP

**Decision:** Use default VPC, allow public IP on EC2 instance

**Rationale:**
- No NAT Gateway ($32/month) or VPC endpoints ($20-30/month) needed
- Instance needs internet for: Docker Hub, S3, SSM
- Security groups restrict all inbound except ALB
- Good for demo/development, documented for production upgrade

**Production Path:** Add VPC endpoints + NAT Gateway before production (documented in `infrastructure/FUTURE_ENHANCEMENTS.md`)

### 4. Model Storage: S3 Cache with Self-Healing

**Decision:** Cache model in S3, implement self-healing export

**Rationale:**
- First instance: Downloads from Ollama (slow), exports to S3
- Subsequent instances: Download from S3 (fast)
- Reduces subsequent RTO from 15 min to 10 min

**Implementation:** Background process exports model after successful download

### 5. Deployment: SSM over SSH

**Decision:** Use AWS Systems Manager for remote access, no SSH keys

**Rationale:**
- No key management overhead
- Audit trail via CloudTrail
- Temporary sessions only
- Industry best practice

### 6. Disk Space: /home vs /tmp for Large Files

**Problem:** Initial implementation downloaded 6.7 GB model to `/tmp` (tmpfs, 1.9 GB capacity), causing failures

**Decision:** Use `/home` for large file operations

**Fix:**
```bash
# Changed from:
aws s3 cp "s3://.../model.tar.gz" /tmp/model.tar.gz

# To:
aws s3 cp "s3://.../model.tar.gz" /home/model.tar.gz
```

**Lesson:** Always check filesystem type and capacity for large operations

### 7. Health Endpoint Design

**Decision:** Return 200 OK in degraded mode, include detailed status

**Rationale:**
- Application is operational (Tesseract works)
- ALB health checks pass
- Clients can inspect `backends` field for capability check
- Fail-open philosophy

**Alternative Rejected:** Return 503 in degraded mode (would mark instance unhealthy unnecessarily)

### 8. Fuzzy Matching Threshold: 90%

**Decision:** Use 90% similarity for brand name matching

**Rationale:**
- Tested with various OCR outputs
- Handles common OCR errors (I→l, O→0)
- Not too lenient (avoids false positives)
- Configurable if needed

**Evidence:** Testing showed 90% catches legitimate OCR errors while rejecting clearly wrong matches

### 9. Product-Specific ABV Tolerances

**Decision:** Different tolerances by product type:
- Wine: ±1.0%
- Spirits: ±0.3%
- Beer: ±0.3%

**Rationale:** Based on TTB regulations (27 CFR 4.36, 5.37, 7.71)

### 10. Test Strategy: Dual Validation (bash + pytest)

**Decision:** Keep both bash test script and pytest suite

**Rationale:**
- Bash tests: Quick smoke tests, familiar to ops
- Pytest: Comprehensive coverage, CI/CD integration
- Not redundant - different use cases

**Coverage:** 55% code coverage achieved (above 50% threshold)

## Implementation Highlights

### Phase 1: Core Validation Logic
- Implemented validators for all required fields
- Fuzzy matching with RapidFuzz
- Product-specific tolerances
- CLI tool for quick testing

### Phase 2: OCR Integration
- Tesseract backend (Pytesseract)
- Ollama backend (llama3.2-vision)
- Unified OCR interface
- Performance benchmarking

### Phase 3: API Development
- FastAPI REST API
- File upload handling
- Batch processing (ZIP files)
- OpenAPI documentation

### Phase 4: Infrastructure
- Terraform/Terragrunt IaC
- Two-layer architecture (foundation + application)
- OIDC for GitHub Actions
- ACM certificate management

### Phase 5: Production Hardening
- Fail-open architecture implementation
- Health endpoint
- Disk space fixes
- Comprehensive documentation

## Challenges & Solutions

### Challenge 1: Ollama Blocking Startup
**Problem:** 15-20 minute RTO waiting for model download  
**Solution:** Lazy initialization + background download  
**Impact:** RTO reduced to 2-3 minutes

### Challenge 2: Disk Space Exhaustion
**Problem:** Model download to `/tmp` (tmpfs) failed at 92 MiB of 6.7 GB  
**Solution:** Use `/home` on root filesystem (42 GB available)  
**Impact:** Model downloads successfully

### Challenge 3: Complex Two-Layer Infrastructure
**Problem:** Risk of destroying protected resources  
**Solution:** Separate foundation (protected) and application (ephemeral) layers  
**Impact:** Safe infrastructure updates

### Challenge 4: Certificate Validation Wait Time
**Problem:** DNS propagation delays during deployment  
**Solution:** Documented manual process, automated retry logic  
**Impact:** Clearer deployment expectations

### Challenge 5: Test Coverage Below Threshold
**Problem:** Initial coverage at 45%  
**Solution:** Added endpoint tests, mocked backends  
**Impact:** Coverage raised to 55%

## Performance Metrics

### OCR Performance
| Backend | Speed | Accuracy | Use Case |
|---------|-------|----------|----------|
| Ollama (llama3.2-vision) | ~58s | ~95% | All verification (only backend) |
| Tesseract (evaluated, rejected) | ~1s | ~60-70% | Not used — accuracy insufficient |

### Infrastructure Performance
| Metric | Old Design | New Design | Improvement |
|--------|-----------|------------|-------------|
| Cold Start RTO | 15-20 min | 2-3 min | 87% faster |
| Warm Start RTO | 8-10 min | 2-3 min | 75% faster |
| Full Capability | 15-20 min | 10-12 min | 40% faster |

### API Performance
- Response time (`POST /verify` sync): ~58 seconds (Ollama)
- Response time (`POST /verify/async` submit): < 1 second (enqueue only)
- Async job completion: ~58 seconds per label
- Batch throughput: 50 labels in ~50 minutes (Ollama, sequential in worker)
- Concurrent requests: Multiple jobs queued and processed by worker

## Testing Summary

**Test Suite:**
- Total tests: 41 passing, 16 skipped
- Code coverage: 55% (above 50% threshold)
- Unit tests: Validators, extractors, parsers
- Integration tests: API endpoints, OCR backends
- E2E tests: Full verification flow

**Key Test Cases:**
- Valid labels (all fields present and correct)
- Invalid labels (missing fields, wrong values)
- OCR error handling (fuzzy matching)
- Batch processing (multiple labels, async)
- Async queue (submit, poll, retry)
- Health endpoint (degraded and healthy modes)

## Production Deployment

**Infrastructure:**
- AWS Region: us-east-1
- Instance Type: g4dn.2xlarge (8 vCPU, 32 GB RAM, GPU, 50 GB disk)
- Load Balancer: Application Load Balancer with HTTPS
- Domain: <configured via domain_name variable>
- Certificate: ACM auto-renewing TLS certificate

**Deployment Method:**
- GitHub Actions CI/CD
- OIDC authentication (no long-lived credentials)
- SSM-based deployment (no SSH)
- Automated testing before deploy

**Operational Status:**
- Health endpoint: `GET /health`
- Monitoring: ALB health checks
- Logging: Docker container logs + CloudWatch
- Access: SSM Session Manager

## Lessons Learned

### What Went Well
1. **Fail-open architecture** - Dramatically improved RTO and user experience
2. **Two-layer infrastructure** - Protected critical resources from accidental deletion
3. **Dual OCR backends** - Flexibility for users, resilience for system
4. **Comprehensive documentation** - Clear guides for deployment and operations
5. **SSM over SSH** - Modern, secure remote access

### What Could Be Improved
1. **Earlier disk space planning** - Should have checked tmpfs capacity earlier
2. **More upfront testing** - Would have caught model download issues sooner
3. **Simpler VPC design** - Custom VPC with private subnets would be better for production
4. **Monitoring/alerting** - Could benefit from CloudWatch dashboards
5. **Rate limiting** - Should implement before high-traffic scenarios

### Technical Debt
1. **Public IP on EC2** - Should add VPC endpoints + NAT Gateway for production
2. **Single instance** - No HA or auto-scaling yet
3. **No metrics endpoint** - Should add Prometheus-compatible metrics
4. **Limited error tracking** - Could integrate Sentry or similar
5. **Manual certificate validation** - Could automate DNS record creation

## Future Enhancements

See `infrastructure/FUTURE_ENHANCEMENTS.md` for detailed proposals:

**High Priority:**
- Remove public IP (VPC endpoints + NAT Gateway)
- Model download progress endpoint
- Enhanced monitoring and alerting

**Medium Priority:**
- Multi-AZ deployment for HA
- Auto-scaling based on load
- Artifact storage for debugging

**Low Priority:**
- Webhooks for batch completion
- ML training pipeline from artifacts
- Performance dashboard

## References

- Full decision log: `docs/DECISION_LOG.md` (comprehensive historical record)
- Original requirements: Consolidated above from `REQUIREMENTS.md`
- Implementation plans: Summarized above from `IMPLEMENTATION_PLAN.md` and `IMPLEMENTATION_SUMMARY.md`
- Project completion: Integrated above from `PROJECT_SUMMARY.md`

---

**Document Purpose:** This consolidated document provides a high-level overview of the project's development journey, key decisions, and outcomes. For detailed decision rationales and historical context, refer to the full `DECISION_LOG.md`.
