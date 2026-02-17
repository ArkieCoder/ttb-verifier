# ACM Certificate for application domain
resource "aws_acm_certificate" "ttb" {
  domain_name       = var.domain_name
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name      = "${var.project_name}-cert"
    Project   = var.project_name
    ManagedBy = "terragrunt"
  }
}

# Interactive pause for DNS validation
resource "terraform_data" "wait_for_certificate_validation" {
  depends_on = [aws_acm_certificate.ttb]

  provisioner "local-exec" {
    command = <<-EOT
      echo ""
      echo "========================================="
      echo "ACTION REQUIRED: DNS Validation"
      echo "========================================="
      echo ""
      echo "Add the following CNAME record to your DNS provider:"
      echo ""
      echo "Record Type: CNAME"
      echo "Name:  ${tolist(aws_acm_certificate.ttb.domain_validation_options)[0].resource_record_name}"
      echo "Value: ${tolist(aws_acm_certificate.ttb.domain_validation_options)[0].resource_record_value}"
      echo ""
      echo "========================================="
      echo "Waiting for DNS propagation and ACM validation..."
      echo "This usually takes 5-30 minutes."
      echo "========================================="
      echo ""
      
      # Wait for certificate to be issued
      CERT_ARN="${aws_acm_certificate.ttb.arn}"
      MAX_ATTEMPTS=60
      ATTEMPT=0
      
      while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
        STATUS=$(aws acm describe-certificate --certificate-arn "$CERT_ARN" --region us-east-1 --query 'Certificate.Status' --output text 2>/dev/null || echo "PENDING")
        
        if [ "$STATUS" = "ISSUED" ]; then
          echo ""
          echo "✅ Certificate validated and issued successfully!"
          echo ""
          exit 0
        elif [ "$STATUS" = "FAILED" ]; then
          echo ""
          echo "❌ Certificate validation failed. Check DNS records."
          echo ""
          exit 1
        fi
        
        echo "⏳ Attempt $((ATTEMPT+1))/$MAX_ATTEMPTS - Status: $STATUS (waiting 30s...)"
        sleep 30
        ATTEMPT=$((ATTEMPT+1))
      done
      
      echo ""
      echo "❌ Timeout: Certificate validation took longer than 30 minutes."
      echo "Please verify DNS records are correct and try again."
      echo ""
      exit 1
    EOT

    interpreter = ["bash", "-c"]
  }
}
