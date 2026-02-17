# ====================================
# Outputs for GitHub Actions Configuration
# ====================================

output "ec2_instance_id" {
  description = "EC2 instance ID - Add to GitHub Secret: EC2_INSTANCE_ID"
  value       = aws_instance.ttb.id
}

output "github_actions_role_arn" {
  description = "IAM role ARN for GitHub Actions - Add to GitHub Secret: AWS_ROLE_TO_ASSUME"
  value       = aws_iam_role.github_actions.arn
}

# ====================================
# Outputs for DNS Configuration
# ====================================

output "alb_dns_name" {
  description = "ALB DNS name - Create CNAME in your DNS provider pointing your domain to this value"
  value       = aws_lb.ttb.dns_name
}

output "certificate_validation_records" {
  description = "DNS records for ACM certificate validation - Add to your DNS provider"
  value = {
    for dvo in aws_acm_certificate.ttb.domain_validation_options : dvo.domain_name => {
      name  = dvo.resource_record_name
      type  = dvo.resource_record_type
      value = dvo.resource_record_value
    }
  }
}

# ====================================
# Additional Outputs for Verification
# ====================================

output "ec2_public_ip" {
  description = "EC2 instance public IP (for direct access if needed)"
  value       = aws_instance.ttb.public_ip
}

output "alb_url" {
  description = "ALB URL for testing"
  value       = "https://ttb-verifier.unitedentropy.com (after DNS configured)"
}

output "certificate_arn" {
  description = "ACM certificate ARN"
  value       = aws_acm_certificate.ttb.arn
}

output "instance_availability_zone" {
  description = "EC2 instance availability zone"
  value       = aws_instance.ttb.availability_zone
}

# ====================================
# Setup Instructions
# ====================================

output "setup_instructions" {
  description = "Next steps after infrastructure is deployed"
  value       = <<-EOT
    
    ========================================
    Infrastructure Deployed Successfully!
    ========================================
    
    NEXT STEPS:
    
    1. ✅ GitHub Secrets configured automatically:
       - AWS_ROLE_TO_ASSUME: ${aws_iam_role.github_actions.arn}
       - EC2_INSTANCE_ID: ${aws_instance.ttb.id}
       - AWS_REGION: us-east-1
    
    2. Add CNAME record to your DNS provider:
       - Hostname: ttb-verifier.unitedentropy.com
       - Type: CNAME
       - Value: ${aws_lb.ttb.dns_name}
    
    3. Wait 5-10 minutes for DNS propagation
    
    4. Test ALB: curl https://ttb-verifier.unitedentropy.com
       (Will show connection error until first GitHub Actions deployment completes)
    
    5. Monitor EC2 initialization: 
       aws ssm start-session --target ${aws_instance.ttb.id}
       docker ps  # Should show ollama container running
    
    ========================================
  EOT
}
