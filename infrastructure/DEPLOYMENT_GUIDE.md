# TTB Verifier Infrastructure Deployment Guide

## Overview

This infrastructure deploys the TTB Verifier application to AWS with full CI/CD automation using GitHub Actions. The deployment is fully configurable to work with any GitHub organization and AWS account.

## Prerequisites

### Required Tools

- Terragrunt (v0.45+)
- OpenTofu (v1.11.5+)
- AWS CLI (v2+)
- GitHub CLI (`gh`)

## Configuration

### 1. Copy and customize the configuration file

```bash
cd infrastructure
cp terraform.tfvars.example terraform.tfvars
```

### 2. Edit `terraform.tfvars` with your settings

```hcl
# Required: Your GitHub organization or username
github_owner = "YourGitHubOrg"

# Required: Repository name (will be created if doesn't exist)
github_repo_name = "ttb-verifier"

# Required: Full domain name for your deployment
domain_name = "ttb-verifier.yourdomain.com"

# Required: Your AWS account ID
aws_account_id = "123456789012"

# Optional: AWS region (default: us-east-1)
aws_region = "us-east-1"

# Optional: EC2 instance type (default: g4dn.2xlarge)
# instance_type = "g4dn.2xlarge"

# Optional: Root volume size in GB (default: 50)
# root_volume_size = 50

# Optional: Environment tag (default: production)
# environment = "production"

# Optional: Additional tags
# tags = {
#   Owner      = "Your Name"
#   CostCenter = "Engineering"
# }
```

### 3. Find your AWS account ID

```bash
aws sts get-caller-identity --query Account --output text
```

## Deployment Steps

### Infrastructure Architecture

The infrastructure is separated into **two layers** with independent Terraform state:

1. **Foundation Layer** (`infrastructure/foundation/`)
   - Protected resources: ACM certificate, GitHub repository, S3 model bucket
   - Deployed once, rarely modified
   - State file: `foundation/terraform.tfstate`

2. **Application Layer** (`infrastructure/`)
   - Ephemeral resources: EC2, Load Balancer, IAM roles, security groups
   - Can be destroyed and recreated safely
   - State file: `infrastructure/terraform.tfstate`

### First-Time Deployment

#### Step 1: Deploy Foundation Layer

The foundation layer contains protected resources that should persist across application deployments.

```bash
cd infrastructure/foundation
export GITHUB_TOKEN=$(gh auth token)
terragrunt init
```

This will:
- Create S3 bucket for Terraform state (if it doesn't exist)
- Create DynamoDB table for state locking (if it doesn't exist)
- Download required provider plugins

**Review the foundation plan:**
```bash
terragrunt plan
```

You should see ~9 resources to be created:
- ACM certificate (for HTTPS)
- GitHub repository and branch protection
- S3 bucket for Ollama models (with versioning, encryption, lifecycle policies)

**Apply foundation infrastructure:**
```bash
terragrunt apply
```

**Important:** This will pause during ACM certificate validation. Follow the prompts to add the DNS CNAME record to your DNS provider.

##### ACM Certificate Validation

When the apply pauses, you'll see output like:

```
ACTION REQUIRED: DNS Validation
=========================================

Add the following CNAME record to your DNS provider:

Record Type: CNAME
Name:  _abc123def456.ttb-verifier.yourdomain.com
Value: _xyz789abc.acm-validations.aws.

=========================================
Waiting for DNS propagation and ACM validation...
```

1. Add the CNAME record to your DNS provider
2. Wait for DNS propagation (5-30 minutes)
3. The infrastructure will automatically continue once validated

**Note:** After the certificate is issued, you can remove this validation CNAME record from your DNS. It's only needed during initial certificate creation. ACM will auto-renew without needing the validation record.

**Foundation outputs** will include:
- `certificate_arn` - Used by application layer Load Balancer
- `s3_bucket_id` - Used by EC2 for model caching
- `repository_name` - Used for GitHub secrets

#### Step 2: Deploy Application Layer

The application layer references foundation resources via Terraform remote state.

```bash
cd infrastructure  # parent directory (application layer)
terragrunt init
```

**Review the application plan:**
```bash
terragrunt plan
```

Review the resources that will be created (~21 AWS resources + 3 GitHub secrets):
- EC2 g4dn.2xlarge instance
- Application Load Balancer + listeners
- Load Balancer target group with health checks
- Security groups (Load Balancer + EC2)
- IAM roles (EC2 SSM + GitHub Actions OIDC)
- GitHub Actions secrets

**Apply application infrastructure:**
```bash
terragrunt apply
```

**Time:** ~5 minutes for AWS resources + 8-15 minutes for EC2 initialization

#### Step 3: Configure DNS CNAME for your application

After `apply` completes, you'll see instructions to add a CNAME record pointing your domain to CloudFront:

```bash
# From the outputs
Hostname: ttb-verifier.yourdomain.com
Type: CNAME
Value: d123456789abcdef.cloudfront.net
```

Add this CNAME to your DNS provider. This record should remain in place permanently.

#### Step 4: Monitor EC2 initialization

The EC2 instance will take 8-15 minutes to fully initialize (Docker, Ollama model download from S3):

```bash
# Get instance ID from outputs
export INSTANCE_ID=$(terragrunt output -raw ec2_instance_id)

# Connect via SSM
aws ssm start-session --target $INSTANCE_ID

# Check Docker containers
docker ps

# Check Ollama model
docker exec ttb-ollama ollama list

# Exit SSM session
exit
```

### 6. Verify GitHub configuration

```bash
# Check that secrets were created
gh secret list --repo ${github_owner}/${github_repo_name}

# Should show:
# AWS_REGION
# AWS_ROLE_TO_ASSUME
# EC2_INSTANCE_ID
```

## Post-Deployment

### Push application code to GitHub

The infrastructure creates an empty repository. You need to push your application code:

```bash
# In the application root directory (not infrastructure/)
cd ..

# Initialize git if not already done
git init
git branch -M master

# Add GitHub remote
git remote add origin git@github.com:${github_owner}/${github_repo_name}.git

# Push code
git add .
git commit -m "Initial commit"
git push -u origin master
```

### Test the deployment

After DNS propagates (5-10 minutes):

```bash
# Health check
curl https://ttb-verifier.yourdomain.com/

# API docs
curl https://ttb-verifier.yourdomain.com/docs

# Test label verification
curl -X POST "https://ttb-verifier.yourdomain.com/verify" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@path/to/label.jpg"
```
