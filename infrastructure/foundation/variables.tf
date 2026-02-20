# ====================================
# Foundation Layer Variables
# These are inherited from parent terragrunt.hcl inputs
# ====================================

variable "github_owner" {
  description = "GitHub organization or user account name"
  type        = string
}

variable "github_repo_name" {
  description = "GitHub repository name"
  type        = string
}

variable "project_name" {
  description = "Project name used for resource naming and tagging"
  type        = string
}

variable "domain_name" {
  description = "Full domain name for the application (e.g., 'ttb-verifier.example.com')"
  type        = string
}

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
}

variable "aws_account_id" {
  description = "AWS account ID"
  type        = string
}
