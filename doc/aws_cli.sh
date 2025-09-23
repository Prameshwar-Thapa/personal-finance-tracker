#!/bin/bash

# Personal Finance Tracker - AWS EKS Deployment Script
# Simple script to deploy Kubernetes cluster and application on AWS EKS

set -e  # Exit on any error

# Configuration Variables
CLUSTER_NAME="finance-tracker-cluster"
REGION="us-east-1"
NODE_GROUP_NAME="finance-tracker-nodes"
NAMESPACE="finance-tracker"

echo "=========================================="
echo "Personal Finance Tracker - EKS Deployment"
echo "=========================================="

# Step 1: Check Prerequisites
echo "Step 1: Checking prerequisites..."

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install it first:"
    echo "curl 'https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip' -o 'awscliv2.zip'"
    echo "unzip awscliv2.zip && sudo ./aws/install"
    exit 1
fi

# Check if eksctl is installed
if ! command -v eksctl &> /dev/null; then
    echo "❌ eksctl not found. Installing eksctl..."
    curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
    sudo mv /tmp/eksctl /usr/local/bin
    echo "✅ eksctl installed successfully"
fi

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Installing kubectl..."
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
    chmod +x kubectl
    sudo mv kubectl /usr/local/bin/
    echo "✅ kubectl installed successfully"
fi

# Check AWS credentials
echo "Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Please run:"
    echo "aws configure"
    exit 1
fi

echo "✅ All prerequisites met!"

# Step 2: Create EKS Cluster
echo ""
echo "Step 2: Creating EKS cluster..."
echo "This will take 10-15 minutes..."

eksctl create cluster \
    --name $CLUSTER_NAME \
    --region $REGION \
    --nodegroup-name $NODE_GROUP_NAME \
    --node-type t3.medium \
    --nodes 2 \
    --nodes-min 1 \
    --nodes-max 4 \
    --managed \
    --with-oidc \
    --ssh-access \
    --ssh-public-key ~/.ssh/id_rsa.pub

echo "✅ EKS cluster created successfully!"

# Step 3: Update kubeconfig
echo ""
echo "Step 3: Updating kubeconfig..."
aws eks update-kubeconfig --region $REGION --name $CLUSTER_NAME

# Verify cluster connection
echo "Verifying cluster connection..."
kubectl get nodes
echo "✅ Connected to EKS cluster!"

# Step 4: Create namespace
echo ""
echo "Step 4: Creating application namespace..."
kubectl create namespace $NAMESPACE
kubectl config set-context --current --namespace=$NAMESPACE
echo "✅ Namespace created and set as default!"

# Step 5: Create secrets
echo ""
echo "Step 5: Creating Kubernetes secrets..."
kubectl create secret generic finance-app-secrets \
    --from-literal=postgres-password=financepass123 \
    --from-literal=secret-key=your-super-secret-key-change-in-production \
    --from-literal=database-url=postgresql://financeuser:financepass123@postgres-service:5432/financedb \
    -n $NAMESPACE

echo "✅ Secrets created!"

# Step 6: Deploy application
echo ""
echo "Step 6: Deploying application to EKS..."

# Apply all Kubernetes manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/postgres-statefulset.yaml
kubectl apply -f k8s/app-deployment.yaml
kubectl apply -f k8s/app-service.yaml

echo "✅ Application deployed!"

# Step 7: Wait for pods to be ready
echo ""
echo "Step 7: Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres --timeout=300s -n $NAMESPACE
kubectl wait --for=condition=ready pod -l app=finance-app --timeout=300s -n $NAMESPACE

echo "✅ All pods are ready!"

# Step 8: Get application URL
echo ""
echo "Step 8: Getting application access information..."

# Get LoadBalancer URL (if using LoadBalancer service)
echo "Getting service information..."
kubectl get services -n $NAMESPACE

# Get external IP
EXTERNAL_IP=$(kubectl get service finance-app-service -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

if [ -z "$EXTERNAL_IP" ]; then
    echo "⏳ LoadBalancer is provisioning. Run this command to check status:"
    echo "kubectl get service finance-app-service -n $NAMESPACE"
    echo ""
    echo "Or use port-forward for immediate access:"
    echo "kubectl port-forward service/finance-app-service 8080:5000 -n $NAMESPACE"
else
    echo "🎉 Application is accessible at: http://$EXTERNAL_IP"
fi

# Step 9: Display useful commands
echo ""
echo "=========================================="
echo "🎉 Deployment Complete!"
echo "=========================================="
echo ""
echo "Useful commands:"
echo "• Check pods: kubectl get pods -n $NAMESPACE"
echo "• Check services: kubectl get services -n $NAMESPACE"
echo "• View logs: kubectl logs -f deployment/finance-app -n $NAMESPACE"
echo "• Port forward: kubectl port-forward service/finance-app-service 8080:5000 -n $NAMESPACE"
echo "• Scale app: kubectl scale deployment finance-app --replicas=3 -n $NAMESPACE"
echo ""
echo "To delete everything:"
echo "eksctl delete cluster --name $CLUSTER_NAME --region $REGION"
echo ""
echo "Cluster info:"
echo "• Cluster name: $CLUSTER_NAME"
echo "• Region: $REGION"
echo "• Namespace: $NAMESPACE"
echo ""
echo "Happy Kubernetes learning! 🚀"
