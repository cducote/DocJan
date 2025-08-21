#!/bin/bash

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <image-tag>"
    exit 1
fi

AWS_REGION="us-east-1"
EC2_INSTANCE_ID="i-058fbddf3468f172d"
NEW_TAG="$1"

echo "Getting ECR repository information..."
ECR_REPO_URI=$(aws ecr describe-repositories --region ${AWS_REGION} --query 'repositories[0].repositoryUri' --output text)

echo "Configuration:"
echo "   ECR Repository: ${ECR_REPO_URI}"
echo "   New Tag: ${NEW_TAG}"
echo "   EC2 Instance: ${EC2_INSTANCE_ID}"

echo "Building Docker image for AMD64 architecture..."
docker build --platform linux/amd64 -t ${NEW_TAG} .

echo "Tagging image for ECR..."
docker tag ${NEW_TAG} ${ECR_REPO_URI}:${NEW_TAG}

echo "Logging into ECR..."
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin $(echo ${ECR_REPO_URI} | cut -d'/' -f1)

echo "Pushing image to ECR..."
docker push ${ECR_REPO_URI}:${NEW_TAG}

echo "Updating EC2 instance..."
EC2_IP=$(aws ec2 describe-instances --instance-ids ${EC2_INSTANCE_ID} --region ${AWS_REGION} --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
echo "EC2 IP: ${EC2_IP}"

CURRENT_IMAGE=$(ssh -i /Users/chrissyd/DocJan/concatly-key.pem -o StrictHostKeyChecking=no ec2-user@${EC2_IP} 'sudo docker inspect concatly-api --format={{.Config.Image}} 2>/dev/null || echo none' | grep -o '[^:]*$' || echo "unknown")
echo "Current running image tag: ${CURRENT_IMAGE}"

ssh -i /Users/chrissyd/DocJan/concatly-key.pem -o StrictHostKeyChecking=no ec2-user@${EC2_IP} << EOF
cd /app
echo "Authenticating with ECR..."
aws ecr get-login-password --region ${AWS_REGION} | sudo docker login --username AWS --password-stdin ${ECR_REPO_URI%/*}
echo "Pulling new image..."
sudo docker pull ${ECR_REPO_URI}:${NEW_TAG}
echo "Testing new container startup..."
if sudo docker run -d --name concatly-api-new -p 8000:8000 -v /app/chroma_store:/app/chroma_store ${ECR_REPO_URI}:${NEW_TAG}; then
    echo "New container started successfully on port 8000"
    sudo docker rename concatly-api-new concatly-api || true
    sudo docker rm app-fastapi-1 || true
else
    echo "Port 8000 busy - doing safe switchover..."
    sudo docker rm concatly-api-new || true
    echo "Stopping old containers..."
    sudo docker stop \$(sudo docker ps -q --filter "publish=8000") || true
    sudo docker rm concatly-api app-fastapi-1 || true
    echo "Starting new container..."
    if sudo docker run -d --name concatly-api -p 8000:8000 -v /app/chroma_store:/app/chroma_store ${ECR_REPO_URI}:${NEW_TAG}; then
        echo "New container started successfully!"
    else
        echo "FAILED TO START NEW CONTAINER!"
        exit 1
    fi
fi
echo "Deployment complete!"
EOF

echo "Deployment completed!"
