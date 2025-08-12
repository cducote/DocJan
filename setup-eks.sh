#!/bin/bash

# EKS Cluster Creation Script for Concatly
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🏗️  EKS Cluster Setup for Concatly${NC}"
echo "=================================="

# Configuration
AWS_REGION=${AWS_REGION:-us-east-1}
CLUSTER_NAME=${CLUSTER_NAME:-concatly-cluster}
NODE_GROUP_NAME=${NODE_GROUP_NAME:-concatly-nodes}
KUBERNETES_VERSION=${KUBERNETES_VERSION:-1.27}

# Check if eksctl is installed
check_eksctl() {
    if ! command -v eksctl &> /dev/null; then
        echo -e "${YELLOW}📦 Installing eksctl...${NC}"
        
        # Install eksctl for macOS
        if [[ "$OSTYPE" == "darwin"* ]]; then
            if command -v brew &> /dev/null; then
                brew tap weaveworks/tap
                brew install weaveworks/tap/eksctl
            else
                echo -e "${RED}❌ Homebrew not found. Please install eksctl manually.${NC}"
                exit 1
            fi
        else
            echo -e "${RED}❌ Please install eksctl manually for your OS.${NC}"
            exit 1
        fi
    fi
    echo -e "${GREEN}✅ eksctl is available${NC}"
}

# Create EKS cluster
create_cluster() {
    echo -e "${YELLOW}🚀 Creating EKS cluster...${NC}"
    echo "Cluster Name: $CLUSTER_NAME"
    echo "Region: $AWS_REGION"
    echo "Kubernetes Version: $KUBERNETES_VERSION"
    echo ""
    
    # Check if cluster already exists
    if eksctl get cluster --name $CLUSTER_NAME --region $AWS_REGION &>/dev/null; then
        echo -e "${YELLOW}⚠️  Cluster $CLUSTER_NAME already exists${NC}"
        return 0
    fi
    
    # Create cluster with eksctl
    eksctl create cluster \
        --name $CLUSTER_NAME \
        --version $KUBERNETES_VERSION \
        --region $AWS_REGION \
        --nodegroup-name $NODE_GROUP_NAME \
        --nodes 2 \
        --nodes-min 1 \
        --nodes-max 4 \
        --node-type t3.medium \
        --managed \
        --with-oidc \
        --ssh-access \
        --ssh-public-key ~/.ssh/id_rsa.pub \
        --enable-ssm
    
    echo -e "${GREEN}✅ EKS cluster created successfully${NC}"
}

# Configure kubectl
configure_kubectl() {
    echo -e "${YELLOW}⚙️  Configuring kubectl...${NC}"
    
    aws eks update-kubeconfig --region $AWS_REGION --name $CLUSTER_NAME
    
    # Verify connection
    kubectl get nodes
    
    echo -e "${GREEN}✅ kubectl configured successfully${NC}"
}

# Install AWS Load Balancer Controller
install_alb_controller() {
    echo -e "${YELLOW}🔧 Installing AWS Load Balancer Controller...${NC}"
    
    # Download IAM policy
    curl -o iam_policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.5.4/docs/install/iam_policy.json
    
    # Create IAM policy
    aws iam create-policy \
        --policy-name AWSLoadBalancerControllerIAMPolicy \
        --policy-document file://iam_policy.json || true
    
    # Create service account
    eksctl create iamserviceaccount \
        --cluster=$CLUSTER_NAME \
        --namespace=kube-system \
        --name=aws-load-balancer-controller \
        --role-name AmazonEKSLoadBalancerControllerRole \
        --attach-policy-arn=arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/AWSLoadBalancerControllerIAMPolicy \
        --approve || true
    
    # Install cert-manager
    kubectl apply \
        --validate=false \
        -f https://github.com/jetstack/cert-manager/releases/download/v1.12.0/cert-manager.yaml
    
    # Install AWS Load Balancer Controller
    curl -Lo v2_5_4_full.yaml https://github.com/kubernetes-sigs/aws-load-balancer-controller/releases/download/v2.5.4/v2_5_4_full.yaml
    sed -i.bak -e "s|your-cluster-name|$CLUSTER_NAME|" v2_5_4_full.yaml
    kubectl apply -f v2_5_4_full.yaml
    
    # Clean up
    rm -f iam_policy.json v2_5_4_full.yaml v2_5_4_full.yaml.bak
    
    echo -e "${GREEN}✅ AWS Load Balancer Controller installed${NC}"
}

# Install EBS CSI driver
install_ebs_csi() {
    echo -e "${YELLOW}💾 Installing EBS CSI driver...${NC}"
    
    eksctl create iamserviceaccount \
        --name ebs-csi-controller-sa \
        --namespace kube-system \
        --cluster $CLUSTER_NAME \
        --role-name AmazonEKS_EBS_CSI_DriverRole \
        --attach-policy-arn arn:aws:iam::aws:policy/service-role/Amazon_EBS_CSI_DriverPolicy \
        --approve || true
    
    eksctl create addon \
        --name aws-ebs-csi-driver \
        --cluster $CLUSTER_NAME \
        --service-account-role-arn arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/AmazonEKS_EBS_CSI_DriverRole \
        --force || true
    
    echo -e "${GREEN}✅ EBS CSI driver installed${NC}"
}

# Main execution
main() {
    check_eksctl
    create_cluster
    configure_kubectl
    install_alb_controller
    install_ebs_csi
    
    echo -e "${GREEN}🎉 EKS cluster setup completed!${NC}"
    echo ""
    echo "Cluster Information:"
    echo "  Name: $CLUSTER_NAME"
    echo "  Region: $AWS_REGION"
    echo "  Kubernetes Version: $KUBERNETES_VERSION"
    echo ""
    echo "Next steps:"
    echo "1. Run ./deploy-eks.sh to deploy your application"
    echo "2. Check cluster status: kubectl get nodes"
    echo "3. View cluster: eksctl get cluster"
}

# Run main function
main "$@"
