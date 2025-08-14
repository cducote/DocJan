#!/bin/bash

# Concatly EKS Terraform Deployment Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Concatly EKS Terraform Deployment${NC}"
echo "===================================="

# Check if Terraform is installed
check_terraform() {
    if ! command -v terraform &> /dev/null; then
        echo -e "${RED}❌ Terraform is not installed${NC}"
        echo "Please install Terraform from: https://www.terraform.io/downloads.html"
        exit 1
    fi
    echo -e "${GREEN}✅ Terraform is installed${NC}"
}

# Check AWS CLI and credentials
check_aws() {
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}❌ AWS CLI is not installed${NC}"
        echo "Please install AWS CLI from: https://aws.amazon.com/cli/"
        exit 1
    fi
    
    if ! aws sts get-caller-identity &> /dev/null; then
        echo -e "${RED}❌ AWS credentials not configured${NC}"
        echo "Please run: aws configure"
        exit 1
    fi
    
    echo -e "${GREEN}✅ AWS CLI is configured${NC}"
}

# Initialize Terraform
init_terraform() {
    echo -e "${YELLOW}🏗️  Initializing Terraform...${NC}"
    cd terraform
    terraform init
    echo -e "${GREEN}✅ Terraform initialized${NC}"
}

# Plan Terraform deployment
plan_terraform() {
    echo -e "${YELLOW}📋 Planning Terraform deployment...${NC}"
    terraform plan -out=tfplan
    echo -e "${GREEN}✅ Terraform plan completed${NC}"
}

# Apply Terraform deployment
apply_terraform() {
    echo -e "${YELLOW}🚀 Applying Terraform deployment...${NC}"
    echo -e "${RED}⚠️  This will create AWS resources and may incur costs!${NC}"
    read -p "Do you want to continue? (y/N): " confirm
    
    if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
        terraform apply tfplan
        echo -e "${GREEN}✅ Terraform deployment completed${NC}"
    else
        echo -e "${YELLOW}Deployment cancelled${NC}"
        exit 1
    fi
}

# Configure kubectl
configure_kubectl() {
    echo -e "${YELLOW}⚙️  Configuring kubectl...${NC}"
    
    # Get cluster name from Terraform output
    CLUSTER_NAME=$(terraform output -raw cluster_name)
    AWS_REGION=$(terraform output -raw cluster_endpoint | grep -o 'us-[a-z]*-[0-9]' | head -1)
    
    if [ -z "$AWS_REGION" ]; then
        AWS_REGION="us-east-1"  # fallback
    fi
    
    aws eks --region $AWS_REGION update-kubeconfig --name $CLUSTER_NAME
    
    # Test connection
    kubectl get nodes
    
    echo -e "${GREEN}✅ kubectl configured successfully${NC}"
}

# Display outputs
build_and_push_docker_image() {
    echo -e "${YELLOW}🐳 Building and pushing Docker image to ECR...${NC}"
    ECR_URL=$(terraform output -raw ecr_repository_url)
    AWS_REGION=$(terraform output -raw cluster_endpoint | grep -o 'us-[a-z]*-[0-9]' | head -1)
    if [ -z "$AWS_REGION" ]; then
        AWS_REGION="us-east-1"
    fi
    read -p "Enter Docker image tag [latest]: " IMAGE_TAG
    IMAGE_TAG=${IMAGE_TAG:-latest}
    echo -e "${YELLOW}Logging in to ECR...${NC}"
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URL
    echo -e "${YELLOW}Building Docker image...${NC}"
    docker build -t concatly-api:$IMAGE_TAG ..
    echo -e "${YELLOW}Tagging Docker image...${NC}"
    docker tag concatly-api:$IMAGE_TAG $ECR_URL:$IMAGE_TAG
    echo -e "${YELLOW}Pushing Docker image to ECR...${NC}"
    docker push $ECR_URL:$IMAGE_TAG
    echo -e "${GREEN}✅ Docker image pushed: $ECR_URL:$IMAGE_TAG${NC}"
}

show_outputs() {
    echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
    echo ""
    echo "Important outputs:"
    echo "=================="
    ECR_URL=$(terraform output -raw ecr_repository_url)
    echo -e "${YELLOW}ECR Repository:${NC} $ECR_URL"
    CLUSTER_NAME=$(terraform output -raw cluster_name)
    echo -e "${YELLOW}Cluster Name:${NC} $CLUSTER_NAME"
    CLUSTER_ENDPOINT=$(terraform output -raw cluster_endpoint)
    echo -e "${YELLOW}Cluster Endpoint:${NC} $CLUSTER_ENDPOINT"
    echo ""
    echo "Next steps:"
    echo "1. Update k8s/deployment.yaml with the ECR image URL and tag if needed."
    echo "2. Deploy your application: kubectl apply -f k8s/"
    echo "3. Get the LoadBalancer URL and update Vercel NEXT_PUBLIC_API_URL"
}

# Cleanup function
cleanup() {
    echo -e "${YELLOW}🧹 Cleaning up temporary files...${NC}"
    rm -f tfplan
}

# Main execution
main() {
    check_terraform
    check_aws
    init_terraform
    plan_terraform
    apply_terraform
    configure_kubectl
    build_and_push_docker_image
    show_outputs
    cleanup
    echo -e "${GREEN}🎉 All done! Your EKS cluster is ready for deployment.${NC}"
}

# Run main function
main "$@"
