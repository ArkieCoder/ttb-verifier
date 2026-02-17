# CloudFront Origin Access Identity for S3 error pages
resource "aws_cloudfront_origin_access_identity" "error_pages" {
  comment = "OAI for TTB Verifier error pages"
}

# CloudFront distribution for custom error pages
resource "aws_cloudfront_distribution" "ttb" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "TTB Label Verifier - Custom Error Pages"
  default_root_object = ""

  # ALB as primary origin
  origin {
    domain_name = aws_lb.ttb.dns_name
    origin_id   = "alb"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  # S3 as error page origin
  origin {
    domain_name = aws_s3_bucket.error_pages.bucket_regional_domain_name
    origin_id   = "s3-error-pages"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.error_pages.cloudfront_access_identity_path
    }
  }

  # Default cache behavior (forward to ALB)
  default_cache_behavior {
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "alb"

    forwarded_values {
      query_string = true
      headers      = ["Host", "Authorization"]

      cookies {
        forward = "all"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 0
    max_ttl                = 0
    compress               = true
  }

  # Custom error response for 503 (unhealthy targets)
  custom_error_response {
    error_code            = 503
    response_code         = 503
    response_page_path    = "/503.html"
    error_caching_min_ttl = 10
  }

  # Custom error response for 502 (bad gateway)
  custom_error_response {
    error_code            = 502
    response_code         = 503
    response_page_path    = "/503.html"
    error_caching_min_ttl = 10
  }

  # Custom error response for 504 (gateway timeout)
  custom_error_response {
    error_code            = 504
    response_code         = 503
    response_page_path    = "/503.html"
    error_caching_min_ttl = 10
  }

  # Use the verified certificate
  aliases = [var.domain_name]

  viewer_certificate {
    acm_certificate_arn      = local.certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  tags = {
    Name      = "ttb-verifier-cloudfront"
    Project   = "ttb-verifier"
    ManagedBy = "terragrunt"
  }
}

# Output CloudFront distribution domain
output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.ttb.domain_name
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = aws_cloudfront_distribution.ttb.id
}
