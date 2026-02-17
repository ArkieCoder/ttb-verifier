# S3 bucket for storing Ollama models
# This significantly reduces RTO by avoiding 5-15 minute model downloads
# from Ollama servers during instance initialization
resource "aws_s3_bucket" "ollama_models" {
  bucket = "${var.project_name}-ollama-models-${var.aws_account_id}"

  tags = {
    Name      = "${var.project_name}-ollama-models"
    Project   = var.project_name
    ManagedBy = "terragrunt"
    Purpose   = "Ollama model storage for fast instance recovery"
  }
}

# Block public access to the models bucket
resource "aws_s3_bucket_public_access_block" "ollama_models" {
  bucket = aws_s3_bucket.ollama_models.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Enable versioning for model safety
resource "aws_s3_bucket_versioning" "ollama_models" {
  bucket = aws_s3_bucket.ollama_models.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "ollama_models" {
  bucket = aws_s3_bucket.ollama_models.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Lifecycle policy to manage costs (optional)
resource "aws_s3_bucket_lifecycle_configuration" "ollama_models" {
  bucket = aws_s3_bucket.ollama_models.id

  rule {
    id     = "transition-old-versions"
    status = "Enabled"

    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "STANDARD_IA"
    }

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
}
