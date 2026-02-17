# Future Enhancements

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
