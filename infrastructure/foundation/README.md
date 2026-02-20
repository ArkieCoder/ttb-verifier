# Foundation Layer - Protected Infrastructure

This directory contains **protected, long-lived resources** that should persist across application deployments. These resources have `prevent_destroy = true` lifecycle rules and are rarely modified after initial deployment.

## Protected Resources

### 1. ACM Certificate (`certificates.tf`)
- **Resource:** `aws_acm_certificate.ttb`
- **Purpose:** HTTPS/TLS certificate for the domain
- **Why Protected:** Avoids 5-30 minute DNS validation wait on recreation
- **ARN exported** to application layer for ALB HTTPS listener

### 2. GitHub Repository (`github_repository.tf`)
- **Resources:** 
  - `github_repository.ttb_verifier` - Main repository
  - `github_branch_protection.master` - Branch protection rules
- **Purpose:** Source code repository and CI/CD configuration
- **Why Protected:** Preserves code, commit history, issues, and settings
- **Repository name exported** to application layer for GitHub secrets

### 3. S3 Model Bucket (`s3_models.tf`)
- **Resources:**
  - `aws_s3_bucket.ollama_models` - Main bucket
  - Associated configurations (versioning, encryption, lifecycle, access controls)
- **Purpose:** Caches Ollama AI model (6.7 GiB) for fast EC2 initialization
- **Why Protected:** Avoids 20-30 minute model download from Ollama on first deploy
- **Bucket ID/ARN exported** to application layer for EC2 access

### 4. OIDC Provider (`oidc.tf`)
- **Resource:** `data.aws_iam_openid_connect_provider.github` (data source)
- **Purpose:** Enables GitHub Actions to authenticate with AWS without credentials
- **Note:** This is a shared OIDC provider (data source, not managed resource)

## State Management

- **State File:** `s3://unitedentropy-ttb-tfstate/foundation/terraform.tfstate`
- **Backend:** Configured via parent `terragrunt.hcl` with `path_relative_to_include()`
- **Locking:** DynamoDB table `unitedentropy-ttb-tfstate`

## Deployment

### First-Time Deployment

```bash
cd infrastructure/foundation
export GITHUB_TOKEN=$(gh auth token)
terragrunt init
terragrunt plan
terragrunt apply
```

**Time:** ~5 minutes (plus 5-30 minutes for ACM certificate validation)

### Outputs

The foundation layer exports these outputs for the application layer:

```hcl
output "certificate_arn"               # ARN of ACM certificate
output "certificate_domain"            # Domain name
output "certificate_validation_records" # DNS validation records
output "s3_bucket_id"                  # S3 bucket name
output "s3_bucket_arn"                 # S3 bucket ARN
output "repository_name"               # GitHub repo name
output "repository_full_name"          # owner/repo format
output "repository_html_url"           # GitHub URL
```

## When to Modify

Modify foundation resources only when:

- **Changing domain name** - Requires new ACM certificate
- **Updating repository settings** - Branch protection rules, visibility, etc.
- **Modifying S3 bucket configuration** - Lifecycle policies, versioning, etc.

## Safety Features

### Prevent Destroy Protection

All resources have `prevent_destroy = true` in their lifecycle configuration:

```hcl
lifecycle {
  prevent_destroy = true
}
```

Attempting to destroy will result in:
```
Error: Instance cannot be destroyed

Resource aws_acm_certificate.ttb has lifecycle.prevent_destroy
set, but the plan calls for this resource to be destroyed.
```

### Removing Protection (Dangerous!)

If you intentionally need to destroy a protected resource:

1. **Remove** `prevent_destroy = true` from the resource definition
2. **Apply** the configuration change: `terragrunt apply`
3. **Destroy** the resource: `terragrunt destroy -target=<resource>`

**Warning:** Destroying foundation resources will:
- Certificate: Require 5-30 minute DNS validation wait on recreation
- Repository: Lose all code, history, issues, and settings
- S3 Bucket: Require 20-30 minute model download on next EC2 initialization

## Variables

Foundation layer inherits these variables from parent `terragrunt.hcl`:

- `github_owner` - GitHub organization/user
- `github_repo_name` - Repository name
- `project_name` - Project identifier
- `domain_name` - Full domain (e.g., ttb-verifier.unitedentropy.com)
- `aws_region` - AWS region
- `aws_account_id` - AWS account ID

## Relationship to Application Layer

The **application layer** (`infrastructure/`) references foundation resources via remote state:

```hcl
# infrastructure/remote_foundation.tf
data "terraform_remote_state" "foundation" {
  backend = "s3"
  config = {
    bucket = "unitedentropy-ttb-tfstate"
    key    = "foundation/terraform.tfstate"
    region = "us-east-1"
  }
}

locals {
  certificate_arn = data.terraform_remote_state.foundation.outputs.certificate_arn
  s3_bucket_id    = data.terraform_remote_state.foundation.outputs.s3_bucket_id
  # ... etc
}
```

This allows the application layer to be destroyed and recreated without affecting foundation resources.

## GitHub Actions

Foundation layer can be deployed via GitHub Actions using the `foundation-deploy.yml` workflow (manual trigger only).

## Troubleshooting

### Certificate Validation Timeout

If ACM certificate validation takes >30 minutes:

1. Verify CNAME record is correct in DNS provider
2. Check DNS propagation: `dig <validation-record>`
3. Re-run `terragrunt apply` - will continue from where it stopped

### State Locking Issues

If state is locked:

```bash
# List locks
aws dynamodb scan --table-name unitedentropy-ttb-tfstate

# Force unlock (use with caution)
terragrunt force-unlock <lock-id>
```

### Accessing Outputs

View foundation outputs:

```bash
cd infrastructure/foundation
terragrunt output
```

## Additional Documentation

- Parent README: [../README.md](../README.md)
- Deployment Guide: [../DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md)
- DNS Configuration: [../DNS_CONFIGURATION.md](../DNS_CONFIGURATION.md)
