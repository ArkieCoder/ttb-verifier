# GitHub OIDC Provider for GitHub Actions authentication
# Allows GitHub Actions to assume AWS IAM roles without long-lived credentials
# Using existing OIDC provider (shared across multiple projects)
data "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"
}
