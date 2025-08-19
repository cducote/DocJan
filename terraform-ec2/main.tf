terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Data sources
data "aws_vpc" "main" {
  id = var.vpc_id
}

data "aws_subnets" "main" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.main.id]
  }
  filter {
    name   = "subnet-id"
    values = ["subnet-0a231214652a257e4"] # us-east-1a PUBLIC subnet
  }
}

# Get all subnets for ALB (across multiple AZs)
# Use specific PUBLIC subnets - one per AZ for ALB internet access
locals {
  alb_subnets = [
    "subnet-0a231214652a257e4", # us-east-1a (PUBLIC)
    "subnet-05e53d1ddd2eb9596", # us-east-1b (PUBLIC)
    "subnet-0f447482aff6255fa"  # us-east-1c (PUBLIC)
  ]
}

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

# Security Group for EC2 instance
resource "aws_security_group" "concatly_api_sg" {
  name_prefix = "concatly-api-"
  vpc_id      = data.aws_vpc.main.id

  # HTTP access (for ALB health checks and direct access)
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS access
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # FastAPI application port
  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # SSH access (for management)
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Restrict this to your IP in production
  }

  # All outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "concatly-api-sg"
  }
}

# IAM role for EC2 instance
resource "aws_iam_role" "ec2_role" {
  name = "concatly-api-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

# IAM policy for EC2 instance (with ECR permissions)
resource "aws_iam_role_policy" "ec2_policy" {
  name = "concatly-api-ec2-policy"
  role = aws_iam_role.ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:GetParametersByPath",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams",
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = "*"
      }
    ]
  })
}

# Instance profile using new role with ECR permissions
resource "aws_iam_instance_profile" "ec2_profile" {
  name = "concatly-api-ec2-profile"
  role = aws_iam_role.ec2_role.name
}

# EBS volume for persistent data
resource "aws_ebs_volume" "app_data" {
  availability_zone = var.availability_zone
  size              = 20
  type              = "gp3"
  encrypted         = true

  tags = {
    Name = "concatly-api-data"
  }
}

# EC2 Instance
resource "aws_instance" "concatly_api" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  key_name              = var.key_pair_name
  vpc_security_group_ids = [aws_security_group.concatly_api_sg.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name
  availability_zone      = var.availability_zone
  subnet_id             = data.aws_subnets.main.ids[0]

  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    docker_image = var.docker_image
    openai_api_key = var.openai_api_key
    clerk_secret_key = var.clerk_secret_key
  }))

  tags = {
    Name = "concatly-api"
  }

  # Don't recreate instance if user_data changes
  lifecycle {
    ignore_changes = [user_data]
  }
}

# Attach EBS volume to EC2 instance
resource "aws_volume_attachment" "app_data_attachment" {
  device_name = "/dev/xvdf"
  volume_id   = aws_ebs_volume.app_data.id
  instance_id = aws_instance.concatly_api.id
}

# Application Load Balancer (optional, for SSL and custom domain)
resource "aws_lb" "concatly_api_alb" {
  count              = var.enable_alb ? 1 : 0
  name               = "concatly-api-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg[0].id]
  subnets            = local.alb_subnets

  enable_deletion_protection = false

  tags = {
    Name = "concatly-api-alb"
  }
}

# Security Group for ALB
resource "aws_security_group" "alb_sg" {
  count       = var.enable_alb ? 1 : 0
  name_prefix = "concatly-api-alb-"
  vpc_id      = data.aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "concatly-api-alb-sg"
  }
}

# Target Group for ALB
resource "aws_lb_target_group" "concatly_api_tg" {
  count    = var.enable_alb ? 1 : 0
  name     = "concatly-api-tg"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = data.aws_vpc.main.id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/ping"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = {
    Name = "concatly-api-tg"
  }
}

# Target Group Attachment
resource "aws_lb_target_group_attachment" "concatly_api_tg_attachment" {
  count            = var.enable_alb ? 1 : 0
  target_group_arn = aws_lb_target_group.concatly_api_tg[0].arn
  target_id        = aws_instance.concatly_api.id
  port             = 8000
}

# ALB Listener (HTTP - redirects to HTTPS)
resource "aws_lb_listener" "concatly_api_http" {
  count             = var.enable_alb ? 1 : 0
  load_balancer_arn = aws_lb.concatly_api_alb[0].arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

# ALB Listener (HTTPS)
resource "aws_lb_listener" "concatly_api_https" {
  count             = var.enable_alb && var.ssl_certificate_arn != "" ? 1 : 0
  load_balancer_arn = aws_lb.concatly_api_alb[0].arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = var.ssl_certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.concatly_api_tg[0].arn
  }
}
