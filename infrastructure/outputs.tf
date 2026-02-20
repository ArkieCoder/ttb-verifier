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

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain - Create CNAME in your DNS provider pointing your domain to this value"
  value       = aws_cloudfront_distribution.ttb.domain_name
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = aws_cloudfront_distribution.ttb.id
}

output "alb_dns_name" {
  description = "ALB DNS name (for reference only - DNS should point to CloudFront, not ALB)"
  value       = aws_lb.ttb.dns_name
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
  value       = "https://${var.domain_name} (after DNS configured)"
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
       - Hostname: ${var.domain_name}
       - Type: CNAME
       - Value: ${aws_cloudfront_distribution.ttb.domain_name}
       
       ⚠️  IMPORTANT: Point to CloudFront, NOT the ALB!
       CloudFront provides custom error pages, caching, and DDoS protection.
    
    3. Wait 5-10 minutes for DNS propagation
    
    4. Test access: curl https://${var.domain_name}/health
       (Will show connection error until first GitHub Actions deployment completes)
    
    5. Monitor EC2 initialization: 
       aws ssm start-session --target ${aws_instance.ttb.id}
       docker ps  # Should show ollama container running
    
    ========================================
    
    CloudFront Distribution: ${aws_cloudfront_distribution.ttb.domain_name}
    ALB (internal use): ${aws_lb.ttb.dns_name}
    
    ========================================
  EOT
}
