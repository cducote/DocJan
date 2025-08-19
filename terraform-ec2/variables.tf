variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "vpc_id" {
  description = "VPC ID to deploy resources in"
  type        = string
  default     = "vpc-0e273858e0ddd6bb1"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.small"  # Start small for testing, can scale up to t3.medium later
}

variable "key_pair_name" {
  description = "Name of the AWS key pair for SSH access"
  type        = string
  default     = "concatly-key" # Update this to your actual key pair name
}

variable "availability_zone" {
  description = "Availability zone for the EC2 instance and EBS volume"
  type        = string
  default     = "us-east-1a"
}

variable "docker_image" {
  description = "Docker image to run on the EC2 instance"
  type        = string
  default     = "your-account.dkr.ecr.us-east-1.amazonaws.com/concatly-api:latest"
}

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
}

variable "clerk_secret_key" {
  description = "Clerk secret key"
  type        = string
  sensitive   = true
}

variable "enable_alb" {
  description = "Whether to create an Application Load Balancer"
  type        = bool
  default     = true
}

variable "ssl_certificate_arn" {
  description = "ARN of the SSL certificate for HTTPS (leave empty to disable HTTPS)"
  type        = string
  default     = ""
}

variable "domain_name" {
  description = "Domain name for the application (optional)"
  type        = string
  default     = ""
}
