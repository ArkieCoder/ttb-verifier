# GitHub Repository Secrets for CI/CD
# These secrets are used by GitHub Actions workflows for deployment

# AWS Role ARN for OIDC authentication (no long-lived credentials)
resource "github_actions_secret" "aws_role_to_assume" {
  repository      = local.repository_name
  secret_name     = "AWS_ROLE_TO_ASSUME"
  plaintext_value = aws_iam_role.github_actions.arn
}

# EC2 Instance ID for SSM deployment commands
resource "github_actions_secret" "ec2_instance_id" {
  repository      = local.repository_name
  secret_name     = "EC2_INSTANCE_ID"
  plaintext_value = aws_instance.ttb.id
}

# AWS Region
resource "github_actions_secret" "aws_region" {
  repository      = local.repository_name
  secret_name     = "AWS_REGION"
  plaintext_value = var.aws_region
}
