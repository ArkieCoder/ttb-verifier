# Manual Infrastructure Deployment Guide

## Overview

A GitHub Actions workflow is available for manually deploying infrastructure changes without requiring local CLI access. This workflow enforces strict concurrency controls to prevent conflicts with application deployments.

## Access the Workflow

**URL**: https://github.com/<github_owner>/<github_repo_name>/actions/workflows/infrastructure-deploy.yml

**Or via GitHub UI**:
1. Navigate to your repository
2. Click the "Actions" tab
3. Select "Infrastructure Deploy" from the left sidebar
4. Click "Run workflow" button (top right)

## Workflow Inputs

### Required Input
- **confirmation**: You must type `APPLY` (all caps) to confirm deployment
  - Safety feature to prevent accidental deployments
  - Workflow fails immediately if not exactly "APPLY"

### Optional Input
- **target**: Target specific resource (leave empty to deploy all)
  - Examples:
    - `aws_instance.ttb` - Update only EC2 instance
    - `aws_security_group.alb` - Update only ALB security group
    - Empty - Apply all changes
  - Uses Terraform `-target` flag

## How It Works

```
Manual Trigger (GitHub UI)
      ↓
Validate Confirmation (must be "APPLY")
      ↓
Checkout Code
      ↓
Install Terragrunt + OpenTofu
      ↓
Configure AWS Credentials (OIDC)
      ↓
Terragrunt Init
      ↓
Terragrunt Plan (with optional -target)
      ↓
Display Plan Summary
      ↓
Terragrunt Apply -auto-approve
      ↓
Show Outputs
      ↓
Deployment Summary
```

## Concurrency Control

### Global Workflow Lock

**All workflows use the same concurrency group**: `{repository}-all-workflows`

**Behavior**:
- ✅ **Queues runs** (doesn't cancel)
- ✅ **Blocks if ANY workflow is running**:
  - Test workflow (PR testing)
  - Deploy workflow (master branch deployments)
  - Terraform Checks (PR validation)
  - Infrastructure Deploy (manual)

**Example Scenario**:
```
10:00 - Deploy workflow starts (push to master)
10:01 - You trigger Infrastructure Deploy
        → Queued, waiting for Deploy to finish
10:03 - Deploy completes
        → Infrastructure Deploy starts automatically
10:10 - Infrastructure Deploy completes
```

### Why This Matters

**Prevents race conditions**:
- Application deployment updating EC2 instance
- Infrastructure deployment modifying EC2 instance
- Both happening simultaneously → unpredictable state

**Trade-off**:
- Safer: No concurrent modifications
- Slower: Must wait for other workflows to complete
- Typical wait: 2-5 minutes for application deploys

## Usage Examples

### Example 1: Deploy All Infrastructure Changes

```
1. Go to: Actions → Infrastructure Deploy → Run workflow
2. Inputs:
   - confirmation: APPLY
   - target: (leave empty)
3. Click "Run workflow"
```

**Use case**: After updating multiple Terraform files (e.g., adding S3 bucket, updating IAM roles)

---

### Example 2: Update Only EC2 Instance

```
1. Go to: Actions → Infrastructure Deploy → Run workflow
2. Inputs:
   - confirmation: APPLY
   - target: aws_instance.ttb
3. Click "Run workflow"
```

**Use case**: Updated `instance_init.sh` or `instance.tf` and want to recreate just the EC2 instance

---

### Example 3: Update IAM Permissions

```
1. Go to: Actions → Infrastructure Deploy → Run workflow
2. Inputs:
   - confirmation: APPLY
   - target: aws_iam_policy.github_actions_ssm
3. Click "Run workflow"
```

**Use case**: Modified IAM policies in `roles.tf`

## Monitoring Progress

### View Live Logs

1. After triggering workflow, you'll be redirected to the run page
2. Click on job name ("Apply Infrastructure Changes")
3. Expand each step to see live output
4. Terragrunt plan and apply output shown in real-time

### Check Workflow Status

```bash
# Via CLI
gh run list --repo <github_owner>/<github_repo_name> --workflow=infrastructure-deploy.yml --limit 5

# View specific run
gh run view <run-id> --repo <github_owner>/<github_repo_name>
```

## Safety Features

### 1. Confirmation Required
- Must type "APPLY" exactly
- Workflow fails immediately if missing or incorrect
- Prevents accidental clicks

### 2. Plan Before Apply
- Always runs `terragrunt plan` first
- Plan output visible in logs
- Shows exactly what will change

### 3. Concurrency Protection
- Won't run if any other workflow is active
- Queues safely until safe to proceed
- No cancellation of in-progress work

### 4. AWS OIDC Authentication
- No long-lived AWS credentials in GitHub
- Temporary credentials per workflow run
- Automatic credential expiration

### 5. Audit Trail
- All runs logged in GitHub Actions
- Timestamps, actor, and outputs recorded
- Can review history of infrastructure changes

## Common Issues

### Issue: Workflow Queued for Long Time

**Symptom**: Workflow shows "Queued" status for several minutes

**Cause**: Another workflow is running (deploy, test, or terraform-checks)

**Solution**: Wait for other workflow to complete, or cancel the other workflow if safe

**Check what's running**:
```bash
gh run list --repo <github_owner>/<github_repo_name> --limit 10
```

---

### Issue: Confirmation Failed

**Symptom**: Workflow fails immediately with "Confirmation failed"

**Cause**: Didn't type "APPLY" exactly (case-sensitive)

**Solution**: Re-run workflow and type "APPLY" in all caps

---

### Issue: Plan Shows Unexpected Changes

**Symptom**: Plan output shows changes you didn't expect

**Cause**: 
- Terraform state drift (manual changes in AWS)
- Someone else modified infrastructure
- Provider version differences

**Solution**: 
1. Review plan output carefully
2. If changes look wrong, cancel the workflow
3. Investigate state drift with local `terragrunt plan`
4. Fix issues locally before re-running workflow

## When to Use

### Use Workflow When:
- ✅ You're away from your local machine
- ✅ Need to deploy from phone/tablet/other device
- ✅ Want deployment history in GitHub Actions
- ✅ Collaborating with team (shared visibility)

### Use Local CLI When:
- ✅ Testing infrastructure changes locally
- ✅ Debugging complex Terraform issues
- ✅ Running `terragrunt plan` frequently during development
- ✅ Need full control over apply process

## Workflow File Location

**File**: `.github/workflows/infrastructure-deploy.yml`

**To modify**:
1. Edit the workflow file
2. Commit and push changes
3. Workflow automatically updates

## Security Considerations

**AWS Credentials**:
- Workflow uses GitHub OIDC (no secrets in GitHub)
- Temporary credentials scoped to specific IAM role
- Role limited to SSM + Terraform operations

**Who Can Trigger**:
- Anyone with "write" access to repository
- Admins can restrict via branch protection
- Consider using GitHub Environments for additional approval gates

**What It Can Do**:
- Create/modify/destroy AWS resources (within IAM permissions)
- Update GitHub repository settings (within GitHub token permissions)
- Cannot: Access other AWS accounts, modify unrelated resources

## Disabling the Workflow

**Temporary disable**:
```bash
gh workflow disable infrastructure-deploy.yml --repo <github_owner>/<github_repo_name>
```

**Permanent disable**:
- Delete `.github/workflows/infrastructure-deploy.yml`
- Or rename to `.github/workflows/infrastructure-deploy.yml.disabled`

## Related Documentation

- `infrastructure/DEPLOYMENT_GUIDE.md` - Full deployment instructions
- `infrastructure/README.md` - Infrastructure overview
- `.github/workflows/deploy.yml` - Application deployment workflow
- `.github/workflows/terraform-checks.yml` - PR validation workflow
