#!/bin/bash
###############################################################################
# TTB Verifier - Secrets Setup Script
# 
# Creates AWS Secrets Manager secrets for UI authentication
#
# Usage:
#   ./scripts/setup_secrets.sh              # Use defaults (takehome/corcos)
#   ./scripts/setup_secrets.sh myuser mypass  # Custom credentials
#
# Production Note:
#   For production deployments, use AWS Cognito instead of Secrets Manager
#   for proper user management, MFA, and federated identity.
#
# Prerequisites:
#   - AWS CLI installed and configured
#   - IAM permissions to create secrets
#   - Secrets are region-specific (ensure correct AWS_REGION)
###############################################################################

set -e

DEFAULT_USER="${1:-takehome}"
DEFAULT_PASS="${2:-corcos}"

echo "========================================="
echo "TTB Verifier - Secrets Setup"
echo "========================================="
echo ""
echo "Creating secrets with:"
echo "  Username: $DEFAULT_USER"
echo "  Password: [hidden]"
echo ""

# Check if secrets already exist
echo "Checking for existing secrets..."

if aws secretsmanager describe-secret --secret-id TTB_DEFAULT_USER >/dev/null 2>&1; then
    echo "⚠️  Secret TTB_DEFAULT_USER already exists. Updating..."
    aws secretsmanager update-secret \
        --secret-id TTB_DEFAULT_USER \
        --secret-string "$DEFAULT_USER"
    echo "✅ Updated TTB_DEFAULT_USER"
else
    echo "Creating TTB_DEFAULT_USER..."
    aws secretsmanager create-secret \
        --name TTB_DEFAULT_USER \
        --secret-string "$DEFAULT_USER" \
        --description "TTB Verifier UI default username"
    echo "✅ Created TTB_DEFAULT_USER"
fi

if aws secretsmanager describe-secret --secret-id TTB_DEFAULT_PASS >/dev/null 2>&1; then
    echo "⚠️  Secret TTB_DEFAULT_PASS already exists. Updating..."
    aws secretsmanager update-secret \
        --secret-id TTB_DEFAULT_PASS \
        --secret-string "$DEFAULT_PASS"
    echo "✅ Updated TTB_DEFAULT_PASS"
else
    echo "Creating TTB_DEFAULT_PASS..."
    aws secretsmanager create-secret \
        --name TTB_DEFAULT_PASS \
        --secret-string "$DEFAULT_PASS" \
        --description "TTB Verifier UI default password"
    echo "✅ Created TTB_DEFAULT_PASS"
fi

echo ""
echo "========================================="
echo "✅ Secrets configured successfully!"
echo "========================================="
echo ""
echo "⚠️  IMPORTANT: For production deployments, use AWS Cognito"
echo "    instead of Secrets Manager for proper user management."
echo ""
echo "Next steps:"
echo "  1. The application will fetch credentials at runtime during login"
echo "  2. Access your application at https://<your-domain>/ui/login"
echo ""
