# ALB Target Group for EC2 instance
resource "aws_lb_target_group" "ttb" {
  name     = "ttb-verifier-tg"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = data.aws_vpc.default.id

  # Health check configuration
  health_check {
    enabled             = true
    path                = "/"
    protocol            = "HTTP"
    port                = "8000"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = "200"
  }

  # Deregistration delay for rolling updates
  deregistration_delay = 30

  tags = {
    Name      = "ttb-verifier-tg"
    Project   = "ttb-verifier"
    ManagedBy = "terragrunt"
  }
}

# Register EC2 instance with target group
resource "aws_lb_target_group_attachment" "ttb" {
  target_group_arn = aws_lb_target_group.ttb.arn
  target_id        = aws_instance.ttb.id
  port             = 8000
}

# Data source for default VPC
data "aws_vpc" "default" {
  default = true
}
