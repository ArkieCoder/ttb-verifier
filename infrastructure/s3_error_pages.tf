# S3 bucket for custom error pages
resource "aws_s3_bucket" "error_pages" {
  bucket = "ttb-verifier-error-pages-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name      = "ttb-verifier-error-pages"
    Project   = "ttb-verifier"
    ManagedBy = "terragrunt"
  }
}

# Block public access by default
resource "aws_s3_bucket_public_access_block" "error_pages" {
  bucket = aws_s3_bucket.error_pages.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Bucket policy to allow CloudFront OAI access
resource "aws_s3_bucket_policy" "error_pages" {
  bucket = aws_s3_bucket.error_pages.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontOAI"
        Effect = "Allow"
        Principal = {
          AWS = aws_cloudfront_origin_access_identity.error_pages.iam_arn
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.error_pages.arn}/*"
      }
    ]
  })
}

# Upload 503 error page
resource "aws_s3_object" "error_503" {
  bucket       = aws_s3_bucket.error_pages.id
  key          = "503.html"
  content      = file("${path.module}/error_pages/503.html")
  content_type = "text/html"
  etag         = filemd5("${path.module}/error_pages/503.html")

  tags = {
    Name      = "503-error-page"
    Project   = "ttb-verifier"
    ManagedBy = "terragrunt"
  }
}

# Data source for current AWS account
data "aws_caller_identity" "current" {}
