# ====================================
# Project Configuration Variables
# ====================================

variable "github_owner" {
  description = "GitHub organization or user account name (e.g., 'ArkieCoder')"
  type        = string
}

variable "github_repo_name" {
  description = "GitHub repository name (e.g., 'ttb-verifier')"
  type        = string
  default     = "ttb-verifier"
}

variable "project_name" {
  description = "Project name used for resource naming and tagging"
  type        = string
  default     = "ttb-verifier"
}

variable "domain_name" {
  description = "Full domain name for the application (e.g., 'ttb-verifier.unitedentropy.com')"
  type        = string
}

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "aws_account_id" {
  description = "AWS account ID"
  type        = string
}

# ====================================
# EC2 Configuration
# ====================================

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium"
}

variable "root_volume_size" {
  description = "Root EBS volume size in GB"
  type        = number
  default     = 30
}

# ====================================
# Tags
# ====================================

variable "environment" {
  description = "Environment name (e.g., 'production', 'staging')"
  type        = string
  default     = "production"
}

variable "tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}
