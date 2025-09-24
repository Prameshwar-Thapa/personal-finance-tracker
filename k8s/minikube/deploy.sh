#!/bin/bash

# Personal Finance Tracker - Minikube Deployment Script
echo "🚀 Starting Personal Finance Tracker deployment on Minikube..."

# Check if minikube is running
if ! minikube status | grep -q "Running"; then
    echo "❌ Minikube is not running. Please start minikube first:"
    echo "   minikube start"
    exit 1
fi

# Enable ingress addon
echo "📦 Enabling ingress addon..."
minikube addons enable ingress

# Apply manifests in order
echo "📋 Applying Kubernetes manifests..."

kubectl apply -f 01-namespace.yaml
echo "✅ Namespace created"

kubectl apply -f 02-storageclass.yaml
echo "✅ StorageClass created"

kubectl apply -f 03-configmap.yaml
echo "✅ ConfigMap created"

kubectl apply -f 04-secrets.yaml
echo "✅ Secrets created"

kubectl apply -f 05-redis.yaml
echo "✅ Redis deployed"

kubectl apply -f 06-postgres.yaml
echo "✅ PostgreSQL StatefulSet created"

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n finance-tracker --timeout=300s

kubectl apply -f 07-pvc.yaml
echo "✅ PVC created"

kubectl apply -f 08-app-deployment.yaml
echo "✅ Application Deployment created"

kubectl apply -f 09-app-service.yaml
echo "✅ Application Service created"

kubectl apply -f 10-ingress.yaml
echo "✅ Ingress created"

# Wait for application to be ready
echo "⏳ Waiting for application to be ready..."
kubectl wait --for=condition=available deployment/finance-app -n finance-tracker --timeout=300s

# Get service URL
echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📊 Deployment Status:"
kubectl get pods -n finance-tracker
echo ""
kubectl get services -n finance-tracker
echo ""
echo "🌐 Access your application:"
echo "   NodePort: $(minikube service finance-app-service -n finance-tracker --url)"
echo "   Ingress: Add '$(minikube ip) finance-tracker.local' to /etc/hosts"
echo "   Then visit: http://finance-tracker.local"
echo ""
echo "🔍 Useful commands:"
echo "   kubectl get all -n finance-tracker"
echo "   kubectl logs -f deployment/finance-app -n finance-tracker"
echo "   minikube dashboard"
