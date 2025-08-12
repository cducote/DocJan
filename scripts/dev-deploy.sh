#!/bin/bash

# Quick development deployment script
set -e

echo "🔧 Development deployment starting..."

# Use a dev tag
IMAGE_TAG="dev-$(date +%s)"
ECR_REPOSITORY="039612881134.dkr.ecr.us-east-1.amazonaws.com/concatly-cluster-api"

# Quick build and deploy
docker build -t concatly-api:$IMAGE_TAG .
docker tag concatly-api:$IMAGE_TAG $ECR_REPOSITORY:$IMAGE_TAG

aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_REPOSITORY
docker push $ECR_REPOSITORY:$IMAGE_TAG

# Update just the image in the running deployment
kubectl set image deployment/concatly-api concatly-api=$ECR_REPOSITORY:$IMAGE_TAG

echo "✅ Dev deployment complete with tag: $IMAGE_TAG"
