output "ec2_instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.concatly_api.id
}

output "ec2_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_instance.concatly_api.public_ip
}

output "ec2_public_dns" {
  description = "Public DNS name of the EC2 instance"
  value       = aws_instance.concatly_api.public_dns
}

output "application_url" {
  description = "URL to access the application"
  value       = var.enable_alb ? "http://${aws_lb.concatly_api_alb[0].dns_name}" : "http://${aws_instance.concatly_api.public_ip}:8000"
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = var.enable_alb ? aws_lb.concatly_api_alb[0].dns_name : null
}

output "alb_zone_id" {
  description = "Zone ID of the Application Load Balancer"
  value       = var.enable_alb ? aws_lb.concatly_api_alb[0].zone_id : null
}

output "ssh_command" {
  description = "Command to SSH into the instance"
  value       = "ssh -i ~/.ssh/${var.key_pair_name}.pem ec2-user@${aws_instance.concatly_api.public_ip}"
}
