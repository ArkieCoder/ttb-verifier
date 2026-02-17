# Future Enhancements

## Network Security: Remove Public IP from EC2 Instance

**Priority:** High (for production)  
**Complexity:** Medium  
**Estimated Effort:** 4-6 hours  
**Status:** Documented, Deferred for Demo Environment  
**Cost Impact:** +$35-60/month

### Current State

The EC2 instance currently receives a public IP address from the default VPC (which has `MapPublicIpOnLaunch = true`). While the security group restricts all inbound access except from the ALB, this configuration is not ideal for production environments.

### Why Public IP Currently Exists

The instance requires internet access for:
1. **Docker Hub**: Pull Docker images (`ollama/ollama`, `python:3.11-slim`)
2. **S3**: Download Ollama model files (6.7 GB)
3. **AWS SSM**: Communicate with Systems Manager for remote access
4. **Package Updates**: Install system packages via `yum`/`dnf`

The default VPC has:
- ❌ No NAT Gateway
- ❌ No VPC Endpoints (S3, SSM, EC2 Messages)
- ✅ Only public subnets with internet gateway

### Security Posture (Current)

**Mitigation in place:**
- Security group only allows port 8000 inbound from ALB security group
- No SSH access configured
- All access via SSM Session Manager (which uses HTTPS)
- Public IP provides no actual access due to security group restrictions

**Risk level:** Low for demo/development, but not production-ready.

### Production Remediation Options

#### Option 1: VPC Endpoints + NAT Gateway (Recommended)

**Changes required:**
1. Create private subnet in default VPC (or new VPC)
2. Deploy NAT Gateway in public subnet (~$32/month + $0.045/GB)
3. Add VPC Endpoints:
   - S3 Gateway Endpoint (free, requires route table update)
   - SSM VPC Endpoint (~$7.30/month)
   - EC2 Messages VPC Endpoint (~$7.30/month)
   - SSM Messages VPC Endpoint (~$7.30/month)
4. Update `instance.tf`:
   ```hcl
   resource "aws_instance" "ttb" {
     subnet_id                   = aws_subnet.private.id
     associate_public_ip_address = false
     # ... rest of config
   }
   ```
5. Update route tables for private subnet

**Total cost:** ~$50-60/month  
**Benefits:**
- No public IP exposure
- Reduced data transfer costs via S3 Gateway Endpoint
- Better security posture for production
- Still allows outbound internet access for Docker Hub

#### Option 2: NAT Gateway Only (Simpler)

**Changes required:**
1. Create private subnet
2. Deploy NAT Gateway in public subnet
3. Update instance to use private subnet without public IP
4. Update route tables

**Total cost:** ~$35-40/month  
**Benefits:**
- Simpler than Option 1 (no VPC endpoints to manage)
- No public IP on instance
- Still requires public internet for all services

**Drawbacks:**
- Higher data transfer costs for S3 (no Gateway Endpoint)
- All SSM traffic goes through NAT instead of VPC Endpoints

#### Option 3: Custom VPC Architecture (Most Robust)

**Changes required:**
1. Create new VPC with CIDR block
2. Create public and private subnets across 2+ AZs
3. Deploy Internet Gateway for public subnets
4. Deploy NAT Gateway in public subnet
5. Add S3 Gateway Endpoint
6. Add SSM VPC Endpoints
7. Migrate all resources to new VPC
8. Update all security group references

**Total cost:** ~$35-50/month  
**Effort:** 8-12 hours  
**Benefits:**
- Clean slate architecture
- Multi-AZ redundancy (if deployed to 2+ NAT Gateways)
- Full control over network topology
- Best practice architecture

### Recommended Implementation Path

**Phase 1 (Current - Demo/Dev):**
- ✅ Keep public IP with security group restrictions
- ✅ Document the limitation (this file + README.md + DEPLOYMENT_GUIDE.md)
- ✅ Accept the risk for non-production environments

**Phase 2 (Pre-Production):**
- Implement Option 1 (VPC Endpoints + NAT Gateway)
- Test all functionality still works (Docker, S3, SSM)
- Validate cost estimates

**Phase 3 (Production):**
- Consider Option 3 (Custom VPC) if scale/redundancy requirements grow
- Add multi-AZ architecture
- Implement VPC Flow Logs for network monitoring

### Implementation Checklist (When Ready)

- [ ] Create Terraform resources for VPC endpoints
- [ ] Create private subnet(s) in default VPC or new VPC
- [ ] Deploy NAT Gateway with Elastic IP
- [ ] Update route tables (private subnet → NAT Gateway, S3 → Gateway Endpoint)
- [ ] Update `instance.tf` with `associate_public_ip_address = false`
- [ ] Update `instance.tf` with `subnet_id` pointing to private subnet
- [ ] Test deployment end-to-end
- [ ] Verify SSM access still works
- [ ] Verify S3 model download still works
- [ ] Verify Docker image pulls still work
- [ ] Update documentation to reflect new architecture
- [ ] Monitor costs for first month

### Cost-Benefit Analysis

| Configuration | Monthly Cost | Security | Complexity |
|--------------|--------------|----------|------------|
| Current (Public IP) | $0 | Medium | Low |
| NAT Gateway Only | ~$35-40 | High | Medium |
| VPC Endpoints + NAT | ~$50-60 | Very High | Medium-High |
| Custom VPC | ~$35-50 | Very High | High |

**Decision for demo environment:** Keep current configuration to minimize costs and complexity while documenting the limitation.

**Decision for production:** Implement Option 1 (VPC Endpoints + NAT Gateway) for optimal security/cost balance.

---

## Model Download Progress Endpoint

**Priority:** Medium  
**Complexity:** Low  
**Estimated Effort:** 2-4 hours  
**Status:** Proposed

### Description

Add a `/model-status` endpoint that provides real-time visibility into Ollama model download progress during EC2 initialization.

### Current Behavior

- Model downloads in background during instance initialization
- No visibility into download progress from API
- Users must SSH or use SSM to check `/var/log/ollama-model-download.log`
- Health endpoint only shows "available" or "unavailable" (binary state)

### Proposed Behavior

**Endpoint:** `GET /model-status`

**Response:**
```json
{
  "model": "llama3.2-vision",
  "status": "downloading",
  "progress": {
    "downloaded_bytes": 3221225472,
    "total_bytes": 7201866752,
    "percentage": 44.7,
    "estimated_time_remaining_seconds": 120
  },
  "source": "s3",
  "started_at": "2026-02-17T20:15:45Z",
  "updated_at": "2026-02-17T20:16:30Z"
}
```

**Status Values:**
- `not_started`: Model download not yet initiated
- `downloading`: Download in progress
- `extracting`: Downloaded, currently extracting
- `ready`: Model fully available
- `error`: Download or extraction failed

### Implementation Notes

1. **Progress Tracking:**
   - Modify `instance_init.sh` to write progress to shared file (e.g., `/var/run/model-status.json`)
   - Parse AWS CLI output or use callback hooks to track download progress
   - Update timestamp on each progress update

2. **API Endpoint:**
   - Read progress file from `/var/run/model-status.json`
   - Return 404 if file doesn't exist (model never attempted)
   - Cache file reads (check every 5 seconds max)

3. **Background Process:**
   - Modify background download process in `instance_init.sh`:
     ```bash
     echo '{"status":"downloading","model":"llama3.2-vision","started_at":"'$(date -Iseconds)'"}' > /var/run/model-status.json
     # Download with progress callback
     aws s3 cp ... | while read line; do
       # Parse progress and update JSON file
     done
     echo '{"status":"ready","model":"llama3.2-vision","completed_at":"'$(date -Iseconds)'"}' > /var/run/model-status.json
     ```

4. **File Permissions:**
   - Ensure progress file is readable by application user
   - Use tmpfs mount for performance (in-memory file)

### Benefits

- Real-time visibility into model download during degraded mode
- Better user experience - know when full functionality will be available
- Operational insight for monitoring/debugging
- Could be displayed in future UI

### Alternatives Considered

1. **WebSocket Streaming:** More complex, requires persistent connections
2. **Server-Sent Events (SSE):** Good for real-time but adds complexity
3. **Simple Polling:** Current proposal - simplest, good enough for this use case

### Dependencies

- None (self-contained enhancement)

### Related Issues

- Resolves lack of visibility during model download
- Complements `/health` endpoint (which only shows binary available/unavailable)

---

## Artifact Storage for Debugging and Audit

### Objective
Store request artifacts (images, extracted text, validation results) in S3 for:
- Debugging failed validations
- Reproducing issues
- Training data collection
- Compliance/audit trail
- Performance analysis and optimization

### Use Cases
1. **Debugging**: When a validation fails unexpectedly, retrieve the original image and validation results
2. **Compliance**: Maintain audit trail of all label verifications for regulatory purposes
3. **Training**: Collect real-world examples to improve OCR and validation accuracy
4. **Analytics**: Analyze patterns in validation failures to identify common issues

### Implementation Overview

#### New Infrastructure Components

**S3 Bucket**:
```hcl
resource "aws_s3_bucket" "artifacts" {
  bucket = "ttb-verifier-artifacts-{account-id}"
}
```

**Bucket Configuration**:
- Versioning: Enabled
- Encryption: AES256 (server-side)
- Public access: Blocked
- Lifecycle policy:
  - S3 Standard: 0-30 days
  - S3 Standard-IA: 30-90 days
  - S3 Glacier: 90-365 days
  - Delete: After 365 days

**IAM Permissions**:
- EC2 role needs `s3:PutObject`, `s3:GetObject` on artifacts bucket
- Optional: Separate IAM user/role for artifact retrieval/analysis

#### API Changes

**Optional Request Parameter**:
```python
@app.post("/verify")
async def verify_label(
    file: UploadFile,
    save_artifact: bool = False,  # New parameter
    ...
):
    # Existing validation logic
    result = await validate_label(file)
    
    # Optionally save to S3
    if save_artifact:
        artifact_id = str(uuid.uuid4())
        await save_to_s3(file, result, artifact_id)
    
    return result
```

**Artifact Structure**:
```
s3://bucket/artifacts/
├── YYYY/
│   ├── MM/
│   │   ├── DD/
│   │   │   ├── {request-id}/
│   │   │   │   ├── image.jpg            # Original uploaded image
│   │   │   │   ├── metadata.json        # Request metadata
│   │   │   │   ├── extracted_text.json  # OCR output
│   │   │   │   └── validation_result.json  # Final validation result
```

**Metadata JSON Structure**:
```json
{
  "request_id": "uuid",
  "timestamp": "2026-02-17T10:30:00Z",
  "client_ip": "1.2.3.4",
  "image_size_bytes": 1234567,
  "image_format": "image/jpeg",
  "ocr_backend": "tesseract",
  "validation_passed": true,
  "processing_time_ms": 1523,
  "model_version": "1.0.0"
}
```

#### API Additions

**Artifact Retrieval Endpoint**:
```python
@app.get("/artifacts/{artifact_id}")
async def get_artifact(artifact_id: str):
    """Retrieve stored artifact by ID"""
    # Download from S3 and return
    pass

@app.get("/artifacts/{artifact_id}/image")
async def get_artifact_image(artifact_id: str):
    """Get original image from artifact"""
    pass

@app.get("/artifacts")
async def list_artifacts(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    validation_status: Optional[str] = None
):
    """List artifacts with filters"""
    # Query S3 and return list
    pass
```

### Implementation Estimate

**Terraform Changes**: ~1 hour
- Create S3 bucket
- Configure lifecycle policies
- Update IAM permissions
- Add outputs for bucket name

**API Changes**: ~3-4 hours
- Add S3 client configuration
- Implement artifact upload logic
- Add metadata generation
- Implement retrieval endpoints
- Add error handling

**Testing**: ~1-2 hours
- Test artifact upload/download
- Verify lifecycle policies
- Test retrieval endpoints
- Load testing with artifacts enabled

**Total Estimate**: 5-7 hours

### Cost Estimate

**Storage**:
- Average image size: 2 MB
- Requests per day: 100
- Storage per month: ~6 GB
- Cost: ~$0.14/month (Standard) + $0.05/month (Standard-IA) + Glacier costs

**API Requests**:
- PUT requests: ~$0.005 per 1000 requests
- GET requests: ~$0.0004 per 1000 requests
- Total API cost: <$1/month for moderate usage

**Total Estimated Monthly Cost**: $1-2/month

### Configuration Options

**Environment Variables**:
```yaml
environment:
  - ARTIFACT_STORAGE_ENABLED=true
  - ARTIFACT_S3_BUCKET=ttb-verifier-artifacts-{account-id}
  - ARTIFACT_DEFAULT_SAVE=false  # Only save when explicitly requested
  - ARTIFACT_RETENTION_DAYS=365
```

### Privacy & Security Considerations

1. **PII**: Label images may contain brand names but typically don't contain PII
2. **Access Control**: Implement IAM policies to restrict who can access artifacts
3. **Encryption**: Use S3 server-side encryption for all artifacts
4. **Compliance**: Ensure retention policies meet regulatory requirements
5. **Data Minimization**: Only store what's necessary for debugging/audit
6. **Right to Delete**: Provide mechanism to delete artifacts on request

### Future Extensions

- **Batch Analysis**: Analyze multiple artifacts to identify patterns
- **ML Training Pipeline**: Automatically extract training data from artifacts
- **Comparison Tool**: Compare OCR results across different backends
- **Performance Dashboard**: Visualize validation metrics over time
- **Anomaly Detection**: Alert on unusual validation patterns
