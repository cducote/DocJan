# Terraform EC2 Deployment for Concatly API

This directory contains Terraform configuration for deploying the Concatly FastAPI application on EC2 instead of EKS for cost optimization.

## Architecture

- **Single EC2 instance** running Docker container
- **Application Load Balancer** for SSL termination and health checks
- **EBS volume** for persistent ChromaDB data
- **IAM roles** with minimal required permissions
- **Security groups** for network access control

## Cost Comparison

| Component | EKS Setup | EC2 Setup |
|-----------|-----------|-----------|
| Control Plane | ~$73/month | $0 |
| Compute | t3.medium nodes | t3.medium instance (~$30/month) |
| Load Balancer | ALB | ALB (~$16/month) |
| Storage | EBS | EBS (~$2/month) |
| **Total** | **~$120-150/month** | **~$48/month** |

## Prerequisites

1. AWS CLI configured with appropriate credentials
2. Terraform installed (>= 1.0)
3. EC2 Key Pair created in your target region
4. Docker image built and pushed to ECR

## Quick Start

1. **Copy variables file:**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

2. **Edit terraform.tfvars:**
   ```hcl
   aws_region = "us-east-1"
   key_pair_name = "your-key-pair-name"
   docker_image = "your-account.dkr.ecr.us-east-1.amazonaws.com/concatly-api:latest"
   openai_api_key = "your-openai-api-key"
   clerk_secret_key = "your-clerk-secret-key"
   ```

   ⚠️ **SECURITY**: `terraform.tfvars` is gitignored and contains secrets. Never commit this file!

3. **Deploy infrastructure:**
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

4. **Access your application:**
   ```bash
   # Get outputs
   terraform output
   
   # Test health endpoint
   curl http://$(terraform output -raw alb_dns_name)/health
   ```

## Files Description

- **main.tf** - Main infrastructure resources
- **variables.tf** - Input variables and their defaults
- **outputs.tf** - Output values after deployment
- **user_data.sh** - EC2 startup script for Docker setup
- **terraform.tfvars.example** - Example variables file

## Features

### Security
- IAM roles with minimal permissions
- Security groups restricting access
- EBS encryption enabled
- Optional SSL/TLS via ALB

### Monitoring
- CloudWatch logs integration
- Application health checks via ALB
- systemd service management

### Persistence
- Dedicated EBS volume for ChromaDB data
- Automatic mounting and formatting
- Data survives instance restarts

### High Availability (Optional)
- Can be extended with Auto Scaling Group
- Multi-AZ deployment via ALB
- Health check-based recovery

## Deployment Commands

```bash
# Initialize Terraform
terraform init

# Plan deployment
terraform plan

# Apply changes
terraform apply

# Destroy infrastructure
terraform destroy
```

## Accessing the Instance

```bash
# SSH into the instance
ssh -i ~/.ssh/your-key-pair.pem ec2-user@$(terraform output -raw ec2_public_ip)

# Check application status
sudo systemctl status concatly-api
docker-compose -f /app/docker-compose.yml ps

# View application logs
docker-compose -f /app/docker-compose.yml logs -f
```

## Troubleshooting

### Application Not Starting
```bash
# Check user data execution
sudo cat /var/log/user-data.log

# Check Docker service
sudo systemctl status docker

# Check application service
sudo systemctl status concatly-api

# Manual start if needed
cd /app && sudo -u ec2-user docker-compose up -d
```

### Health Check Failures
```bash
# Test health endpoint locally
curl http://localhost:8000/health

# Check application logs
docker-compose -f /app/docker-compose.yml logs fastapi
```

### Data Persistence Issues
```bash
# Check EBS volume mounting
df -h | grep xvdf

# Check data directory permissions
ls -la /app/data
```

## Migration from EKS

1. **Backup data** from EKS persistent volumes
2. **Deploy EC2 infrastructure** using this configuration
3. **Copy data** to new EBS volume
4. **Update DNS** to point to new ALB
5. **Verify functionality** 
6. **Decommission EKS** resources

## Scaling Considerations

### When to Scale Up
- CPU/Memory consistently >80%
- Response times increasing
- Multiple concurrent users

### Scaling Options
1. **Vertical scaling** - larger instance type
2. **Auto Scaling Group** - multiple instances
3. **Return to EKS** - when complexity justifies cost

## Security Notes

- Restrict SSH access to your IP in production
- Use AWS Secrets Manager for sensitive values
- Enable CloudTrail for audit logging
- Regular security updates via user data script

## Monitoring

- **CloudWatch Metrics** - EC2 and application metrics
- **CloudWatch Logs** - Application logs
- **ALB Health Checks** - Application availability
- **Custom Health Script** - `/app/health-check.sh`
