#!/bin/bash

# Concatly API EKS Deployment Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Concatly API EKS Deployment Script${NC}"
echo "=================================="

# Configuration
AWS_REGION=${AWS_REGION:-us-east-1}
CLUSTER_NAME=${CLUSTER_NAME:-concatly-cluster}
ECR_REPOSITORY=${ECR_REPOSITORY:-concatly-api}
IMAGE_TAG=${IMAGE_TAG:-latest}

# Check if required tools are installed
check_dependencies() {
    echo -e "${YELLOW}📋 Checking dependencies...${NC}"
    
    commands=("aws" "kubectl" "docker")
    for cmd in "${commands[@]}"; do
        if ! command -v $cmd &> /dev/null; then
            echo -e "${RED}❌ $cmd is not installed${NC}"
            exit 1
        fi
    done
    echo -e "${GREEN}✅ All dependencies found${NC}"
}

# Create ECR repository if it doesn't exist
create_ecr_repo() {
    echo -e "${YELLOW}🏗️  Creating ECR repository...${NC}"
    
    aws ecr describe-repositories --repository-names $ECR_REPOSITORY --region $AWS_REGION &>/dev/null || {
        echo "Creating ECR repository: $ECR_REPOSITORY"
        aws ecr create-repository --repository-name $ECR_REPOSITORY --region $AWS_REGION
    }
    
    # Get ECR login token
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $(aws ecr describe-repositories --repository-names $ECR_REPOSITORY --region $AWS_REGION --query 'repositories[0].repositoryUri' --output text | cut -d'/' -f1)
}

# Build and push Docker image
build_and_push() {
    echo -e "${YELLOW}🔨 Building and pushing Docker image...${NC}"
    
    # Get ECR repository URI
    ECR_URI=$(aws ecr describe-repositories --repository-names $ECR_REPOSITORY --region $AWS_REGION --query 'repositories[0].repositoryUri' --output text)
    
    # Build image
    echo "Building image: $ECR_URI:$IMAGE_TAG"
    docker build -t $ECR_URI:$IMAGE_TAG .
    
    # Push image
    echo "Pushing image to ECR..."
    docker push $ECR_URI:$IMAGE_TAG
    
    # Update deployment.yaml with correct image
    sed -i.bak "s|image: concatly-api:latest|image: $ECR_URI:$IMAGE_TAG|g" k8s/deployment.yaml
    
    echo -e "${GREEN}✅ Image built and pushed successfully${NC}"
}

# Encode secrets
encode_secrets() {
    echo -e "${YELLOW}🔐 Encoding secrets...${NC}"
    
    # Check if .env file exists
    if [ -f ".env" ]; then
        source .env
    else
        echo -e "${YELLOW}⚠️  No .env file found. Please set OPENAI_API_KEY manually${NC}"
        read -p "Enter your OpenAI API Key: " OPENAI_API_KEY
    fi
    
    # Base64 encode the API key
    ENCODED_KEY=$(echo -n "$OPENAI_API_KEY" | base64)
    
    # Update secrets.yaml
    sed -i.bak "s|openai-api-key: \"\"|openai-api-key: \"$ENCODED_KEY\"|g" k8s/secrets.yaml
    
    echo -e "${GREEN}✅ Secrets encoded${NC}"
}

# Deploy to EKS
deploy_to_eks() {
    echo -e "${YELLOW}🚢 Deploying to EKS...${NC}"
    
    # Update kubeconfig
    aws eks update-kubeconfig --region $AWS_REGION --name $CLUSTER_NAME
    
    # Apply Kubernetes manifests
    echo "Applying Kubernetes manifests..."
    kubectl apply -f k8s/pvc.yaml
    kubectl apply -f k8s/secrets.yaml
    kubectl apply -f k8s/deployment.yaml
    kubectl apply -f k8s/service.yaml
    
    echo -e "${GREEN}✅ Deployment completed${NC}"
    
    # Wait for service to get external IP
    echo -e "${YELLOW}⏳ Waiting for LoadBalancer to get external IP...${NC}"
    kubectl wait --for=condition=ready pod -l app=concatly-api --timeout=300s
    
    # Get service URL
    EXTERNAL_IP=$(kubectl get service concatly-api-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    if [ -n "$EXTERNAL_IP" ]; then
        echo -e "${GREEN}🎉 Service is available at: http://$EXTERNAL_IP${NC}"
        echo -e "${YELLOW}📝 Update your Vercel NEXT_PUBLIC_API_URL to: http://$EXTERNAL_IP${NC}"
    else
        echo -e "${YELLOW}⏳ LoadBalancer IP not ready yet. Check with: kubectl get service concatly-api-service${NC}"
    fi
}

# Main execution
main() {
    check_dependencies
    create_ecr_repo
    build_and_push
    encode_secrets
    deploy_to_eks
    
    echo -e "${GREEN}🎉 Deployment script completed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Check pod status: kubectl get pods"
    echo "2. Check service status: kubectl get service concatly-api-service"
    echo "3. Check logs: kubectl logs -l app=concatly-api"
    echo "4. Update your Vercel environment variable with the LoadBalancer URL"
}

# Run main function
main "$@"
