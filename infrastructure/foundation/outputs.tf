# Foundation Layer Outputs
# These outputs are consumed by the application layer via remote state

output "certificate_arn" {
  description = "ARN of the ACM certificate for HTTPS"
  value       = aws_acm_certificate.ttb.arn
}

output "certificate_domain" {
  description = "Domain name of the ACM certificate"
  value       = aws_acm_certificate.ttb.domain_name
}

output "certificate_validation_records" {
  description = "DNS records needed for certificate validation"
  value = [
    for dvo in aws_acm_certificate.ttb.domain_validation_options : {
      name   = dvo.resource_record_name
      type   = dvo.resource_record_type
      value  = dvo.resource_record_value
    }
  ]
}

output "s3_bucket_id" {
  description = "ID (name) of the S3 bucket for Ollama models"
  value       = aws_s3_bucket.ollama_models.id
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket for Ollama models"
  value       = aws_s3_bucket.ollama_models.arn
}

output "repository_name" {
  description = "GitHub repository name"
  value       = github_repository.ttb_verifier.name
}

output "repository_full_name" {
  description = "Full name of GitHub repository (owner/repo)"
  value       = github_repository.ttb_verifier.full_name
}

output "repository_html_url" {
  description = "HTML URL of the GitHub repository"
  value       = github_repository.ttb_verifier.html_url
}
