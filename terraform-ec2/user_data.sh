#!/bin/bash

# Update system
yum update -y

# Install Docker
yum install -y docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install CloudWatch agent
yum install -y amazon-cloudwatch-agent

# Create application directory
mkdir -p /app
chown ec2-user:ec2-user /app

# Format and mount EBS volume for persistent data
while [ ! -e /dev/xvdf ]; do sleep 1; done
file -s /dev/xvdf | grep -q ": data$" && mkfs -t ext4 /dev/xvdf
mkdir -p /app/data
mount /dev/xvdf /app/data
echo '/dev/xvdf /app/data ext4 defaults,nofail 0 2' >> /etc/fstab
chown ec2-user:ec2-user /app/data

# Install AWS CLI if not present
yum install -y aws-cli

# Authenticate Docker with ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 039612881134.dkr.ecr.us-east-1.amazonaws.com

# Create Docker Compose file
cat > /app/docker-compose.yml << 'EOF'
version: '3.8'

services:
  fastapi:
    image: ${docker_image}
    ports:
      - "8000:8000"
    restart: unless-stopped
    volumes:
      - /app/data:/app/chroma_store
    environment:
      - OPENAI_API_KEY=${openai_api_key}
      - CLERK_SECRET_KEY=${clerk_secret_key}
      - CHROMA_PERSIST_DIR=/app/chroma_store
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/ping"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    logging:
      driver: "awslogs"
      options:
        awslogs-group: "/aws/ec2/concatly-api"
        awslogs-region: "us-east-1"
        awslogs-create-group: "true"
EOF

chown ec2-user:ec2-user /app/docker-compose.yml

# Create systemd service for the application
cat > /etc/systemd/system/concatly-api.service << 'EOF'
[Unit]
Description=Concatly API Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=true
WorkingDirectory=/app
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
User=ec2-user
Group=ec2-user

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
systemctl daemon-reload
systemctl enable concatly-api.service

# Wait for Docker to be ready and start the application
sleep 30
systemctl start concatly-api.service

# Create a simple health check script
cat > /app/health-check.sh << 'EOF'
#!/bin/bash
curl -f http://localhost:8000/health > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "Application is healthy"
    exit 0
else
    echo "Application is unhealthy"
    exit 1
fi
EOF

chmod +x /app/health-check.sh
chown ec2-user:ec2-user /app/health-check.sh

# Create log rotation for application logs
cat > /etc/logrotate.d/concatly-api << 'EOF'
/var/log/concatly-api/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 ec2-user ec2-user
}
EOF

echo "User data script completed successfully" >> /var/log/user-data.log
