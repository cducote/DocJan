#!/bin/bash

# Build and Deploy Script for FastAPI to EKS
set -e

# Parse command line arguments
FORCE_BUILD=false
SKIP_BUILD=false
DEPLOY_ONLY=false
IMAGE_TAG="latest"

while [[ $# -gt 0 ]]; do
  case $1 in
    --force-build)
      FORCE_BUILD=true
      shift
      ;;
    --skip-build)
      SKIP_BUILD=true
      shift
      ;;
    --deploy-only)
      DEPLOY_ONLY=true
      SKIP_BUILD=true
      shift
      ;;
    --tag)
      IMAGE_TAG="$2"
      shift 2
      ;;
    *)
      IMAGE_TAG="$1"
      shift
      ;;
  esac
done

echo "🚀 Starting deployment process..."
echo "📝 Image tag: $IMAGE_TAG"
echo "🔧 Options: Force build=$FORCE_BUILD, Skip build=$SKIP_BUILD, Deploy only=$DEPLOY_ONLY"

# Change to project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"
echo "📁 Working from project root: $(pwd)"

# Configuration
AWS_REGION="us-east-1"
ECR_REPOSITORY="039612881134.dkr.ecr.us-east-1.amazonaws.com/concatly-cluster-api"
CLUSTER_NAME="concatly-cluster"

# Function to check if image exists in ECR
check_image_exists() {
    echo "🔍 Checking if image $ECR_REPOSITORY:$IMAGE_TAG exists in ECR..."
    if aws ecr describe-images --repository-name "concatly-cluster-api" --image-ids imageTag=$IMAGE_TAG --region $AWS_REGION >/dev/null 2>&1; then
        echo "✅ Image $IMAGE_TAG found in ECR"
        return 0
    else
        echo "❌ Image $IMAGE_TAG not found in ECR"
        return 1
    fi
}

# Function to check if image exists locally
check_local_image_exists() {
    echo "🔍 Checking if image concatly-api:$IMAGE_TAG exists locally..."
    if docker image inspect concatly-api:$IMAGE_TAG >/dev/null 2>&1; then
        echo "✅ Image $IMAGE_TAG found locally"
        return 0
    else
        echo "❌ Image $IMAGE_TAG not found locally"
        return 1
    fi
}

# Build and push logic
if [ "$SKIP_BUILD" = false ]; then
    # Check if we need to build
    NEED_BUILD=true
    
    if [ "$FORCE_BUILD" = false ]; then
        if check_image_exists; then
            echo "🎯 Image already exists in ECR. Use --force-build to rebuild anyway."
            NEED_BUILD=false
        elif check_local_image_exists; then
            echo "🎯 Image exists locally but not in ECR. Will tag and push existing image."
            NEED_BUILD=false
        fi
    fi

    if [ "$NEED_BUILD" = true ]; then
        # Step 1: Build Docker image
        echo "📦 Building Docker image for AMD64 architecture..."
        docker build --platform linux/amd64 -t concatly-api:$IMAGE_TAG .
    fi

    # Step 2: Tag for ECR (always needed for push)
    echo "🏷️  Tagging image for ECR..."
    docker tag concatly-api:$IMAGE_TAG $ECR_REPOSITORY:$IMAGE_TAG

    # Step 3: Login to ECR
    echo "🔐 Logging into ECR..."
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPOSITORY

    # Step 4: Push to ECR (only if not already there or forced)
    if [ "$NEED_BUILD" = true ] || [ "$FORCE_BUILD" = true ] || ! check_image_exists; then
        echo "⬆️  Pushing image to ECR..."
        docker push $ECR_REPOSITORY:$IMAGE_TAG
    else
        echo "⏭️  Skipping push - image already in ECR"
    fi
else
    echo "⏭️  Skipping build and push (--skip-build or --deploy-only specified)"
    # Still check if the image exists in ECR
    if ! check_image_exists; then
        echo "❌ Error: Image $IMAGE_TAG not found in ECR and build was skipped!"
        echo "💡 Available options:"
        echo "   - Remove --skip-build to allow building"
        echo "   - Use a different --tag that exists in ECR"
        echo "   - Push the image manually first"
        exit 1
    fi
fi

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

# Usage examples:
echo ""
echo "📖 Usage examples:"
echo "  ./deploy.sh                          # Build and deploy with 'latest' tag"
echo "  ./deploy.sh v1.2.3                   # Build and deploy with 'v1.2.3' tag"
echo "  ./deploy.sh --tag v1.2.3             # Same as above"
echo "  ./deploy.sh --force-build v1.2.3     # Force rebuild even if image exists"
echo "  ./deploy.sh --skip-build v1.2.3      # Deploy existing image without building"
echo "  ./deploy.sh --deploy-only v1.2.3     # Only deploy (alias for --skip-build)"
