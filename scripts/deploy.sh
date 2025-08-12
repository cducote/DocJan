#!/bin/bash

# Build and Deploy Script for FastAPI to EKS
set -e

echo "🚀 Starting deployment process..."

# Configuration
AWS_REGION="us-east-1"
ECR_REPOSITORY="039612881134.dkr.ecr.us-east-1.amazonaws.com/concatly-cluster-api"
CLUSTER_NAME="concatly-cluster"
IMAGE_TAG=${1:-latest}

# Step 1: Build Docker image
echo "📦 Building Docker image..."
docker build -t concatly-api:$IMAGE_TAG .

# Step 2: Tag for ECR
echo "🏷️  Tagging image for ECR..."
docker tag concatly-api:$IMAGE_TAG $ECR_REPOSITORY:$IMAGE_TAG

# Step 3: Login to ECR
echo "🔐 Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPOSITORY

# Step 4: Push to ECR
echo "⬆️  Pushing image to ECR..."
docker push $ECR_REPOSITORY:$IMAGE_TAG

# Step 5: Update Kubernetes deployment
echo "🔄 Updating Kubernetes deployment..."
# Update image in deployment file
sed -i.bak "s|image: .*|image: $ECR_REPOSITORY:$IMAGE_TAG|" k8s/deployment.yaml

# Step 6: Apply to cluster
echo "☸️  Applying to EKS cluster..."
kubectl apply -f k8s/

# Step 7: Wait for rollout
echo "⏳ Waiting for deployment to complete..."
kubectl rollout status deployment/concatly-api

# Step 8: Get LoadBalancer URL
echo "🌐 Getting LoadBalancer URL..."
LB_URL=$(kubectl get svc concatly-api-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo "✅ Deployment complete!"
echo "🔗 API URL: http://$LB_URL"

# Restore original deployment file
mv k8s/deployment.yaml.bak k8s/deployment.yaml

echo "🎉 All done! Your FastAPI is now running on EKS."
