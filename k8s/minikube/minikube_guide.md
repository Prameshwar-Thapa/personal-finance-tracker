# Personal Finance Tracker - Minikube Deployment Guide

## 🎯 Overview

This guide provides step-by-step instructions to deploy the Personal Finance Tracker application on Minikube. The application demonstrates a complete microservices architecture with persistent storage, database management, and ingress configuration.

## 🏗️ Architecture Components

### Application Stack
- **Frontend/Backend**: Flask web application (Python)
- **Database**: PostgreSQL 13 with persistent storage
- **Cache**: Redis 7 for session storage and caching
- **File Storage**: Persistent volume for receipt uploads
- **Load Balancing**: Kubernetes Service with NodePort
- **Ingress**: NGINX Ingress Controller for external access

### Kubernetes Resources Used

#### 1. **Namespace** (`01-namespace.yaml`)
- **Purpose**: Logical isolation of resources
- **Why**: Separates finance tracker resources from other applications
- **Benefits**: Resource organization, security boundaries, easier management

#### 2. **StorageClass** (`02-storageclass.yaml`)
- **Purpose**: Defines storage provisioning policy
- **Provisioner**: `k8s.io/minikube-hostpath` (Minikube-specific)
- **Why**: Enables dynamic volume provisioning for persistent storage
- **Reclaim Policy**: Retain (data persists after PVC deletion)

#### 3. **ConfigMap** (`03-configmap.yaml`)
- **Purpose**: Non-sensitive configuration data
- **Contains**: Flask environment, upload paths, database names
- **Why**: Separates configuration from application code
- **Benefits**: Easy configuration updates without rebuilding images

#### 4. **Secrets** (`04-secrets.yaml`)
- **Purpose**: Sensitive data storage (passwords, keys)
- **Contains**: Database credentials, Flask secret key, connection strings
- **Why**: Secure handling of sensitive information
- **Encoding**: Base64 encoded values

#### 5. **Redis Deployment** (`05-redis.yaml`)
- **Purpose**: In-memory caching and session storage
- **Why Deployment**: 
  - Stateless caching service
  - Easy horizontal scaling
  - Fast restart capability
- **Image**: redis:7-alpine (lightweight)
- **Use Cases**: Session storage, query caching, rate limiting

#### 6. **PostgreSQL StatefulSet** (`06-postgres.yaml`)
- **Purpose**: Database deployment with persistent storage
- **Why StatefulSet**: 
  - Stable network identity
  - Ordered deployment/scaling
  - Persistent storage per pod
  - Stable hostname (postgres-0)
- **Headless Service**: Direct pod-to-pod communication
- **Volume Claim Template**: Automatic PVC creation per replica

#### 7. **PersistentVolumeClaim** (`07-pvc.yaml`)
- **Purpose**: Request storage for file uploads
- **Why**: Persistent storage for receipt images
- **Access Mode**: ReadWriteOnce (single node access)
- **Storage**: 1Gi for uploaded files

#### 8. **Application Deployment** (`08-app-deployment.yaml`)
- **Purpose**: Flask application deployment
- **Init Container**: Waits for PostgreSQL readiness
- **Why Deployment**: 
  - Stateless application
  - Rolling updates
  - Horizontal scaling
  - Self-healing
- **Probes**: Health checks for reliability

#### 9. **Service** (`09-app-service.yaml`)
- **Purpose**: Load balancing and service discovery
- **Type**: NodePort (external access in Minikube)
- **Why**: Stable endpoint for application access

#### 10. **Ingress** (`10-ingress.yaml`)
- **Purpose**: HTTP/HTTPS routing and SSL termination
- **Controller**: NGINX Ingress
- **Why**: Production-like external access with domain names

## 📋 Prerequisites

### System Requirements
- **CPU**: 2+ cores
- **Memory**: 4GB+ RAM
- **Storage**: 10GB+ free space
- **OS**: Linux, macOS, or Windows

### Required Software
```bash
# Docker
docker --version

# Minikube
minikube version

# kubectl
kubectl version --client

# Optional: Helm
helm version
```

## 🚀 Installation Steps

### 1. Install Prerequisites

#### Install Docker
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install docker.io
sudo usermod -aG docker $USER

# macOS (using Homebrew)
brew install docker

# Windows: Download Docker Desktop
```

#### Install Minikube
```bash
# Linux
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# macOS
brew install minikube

# Windows (using Chocolatey)
choco install minikube
```

#### Install kubectl
```bash
# Linux
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# macOS
brew install kubectl

# Windows
choco install kubernetes-cli
```

### 2. Start Minikube

```bash
# Start Minikube with recommended resources
minikube start --driver=docker --memory=4096 --cpus=2

# Verify installation
minikube status
kubectl cluster-info
```

### 3. Enable Required Addons

```bash
# Enable ingress controller
minikube addons enable ingress

# Verify ingress controller
kubectl get pods -n ingress-nginx
```

## 🛠️ Deployment Process

### Method 1: Automated Deployment (Recommended)

```bash
# Navigate to minikube directory
cd k8s/minikube

# Run deployment script
./deploy.sh
```

### Method 2: Manual Step-by-Step Deployment

#### Step 1: Create Namespace
```bash
kubectl apply -f 01-namespace.yaml
kubectl get namespaces
```

#### Step 2: Setup Storage
```bash
kubectl apply -f 02-storageclass.yaml
kubectl get storageclass
```

#### Step 3: Configure Application
```bash
kubectl apply -f 03-configmap.yaml
kubectl apply -f 04-secrets.yaml

# Verify configuration
kubectl get configmap -n finance-tracker
kubectl get secrets -n finance-tracker
```

#### Step 4: Deploy Services
```bash
kubectl apply -f 05-redis.yaml
kubectl apply -f 06-postgres.yaml

# Wait for services to be ready
kubectl wait --for=condition=ready pod -l app=redis -n finance-tracker --timeout=300s
kubectl wait --for=condition=ready pod -l app=postgres -n finance-tracker --timeout=300s

# Verify deployments
kubectl get pods -n finance-tracker
```

#### Step 5: Setup Application Storage
```bash
kubectl apply -f 07-pvc.yaml
kubectl get pvc -n finance-tracker
```

#### Step 6: Deploy Application
```bash
kubectl apply -f 08-app-deployment.yaml

# Wait for application to be ready
kubectl wait --for=condition=available deployment/finance-app -n finance-tracker --timeout=300s

# Verify application deployment
kubectl get deployment -n finance-tracker
kubectl get pods -n finance-tracker
```

#### Step 7: Expose Application
```bash
kubectl apply -f 09-app-service.yaml
kubectl apply -f 10-ingress.yaml

# Verify services
kubectl get service -n finance-tracker
kubectl get ingress -n finance-tracker
```

## 🌐 Accessing the Application

### Method 1: NodePort Service
```bash
# Get service URL
minikube service finance-app-service -n finance-tracker --url

# Example output: http://192.168.49.2:30080
# Open this URL in your browser
```

### Method 2: Ingress (Domain-based)
```bash
# Get Minikube IP
minikube ip

# Add to /etc/hosts (Linux/macOS) or C:\Windows\System32\drivers\etc\hosts (Windows)
echo "$(minikube ip) finance-tracker.local" | sudo tee -a /etc/hosts

# Access via domain
open http://finance-tracker.local
```

### Method 3: Port Forwarding
```bash
# Forward local port to service
kubectl port-forward -n finance-tracker service/finance-app-service 8080:80

# Access via localhost
open http://localhost:8080
```

## 🔍 Monitoring and Troubleshooting

### Check Deployment Status
```bash
# Overview of all resources
kubectl get all -n finance-tracker

# Detailed pod information
kubectl describe pods -n finance-tracker

# Check resource usage
kubectl top pods -n finance-tracker
kubectl top nodes
```

### View Logs
```bash
# Application logs
kubectl logs -f deployment/finance-app -n finance-tracker

# Database logs
kubectl logs -f statefulset/postgres -n finance-tracker

# Previous container logs (if pod restarted)
kubectl logs deployment/finance-app -n finance-tracker --previous
```

### Debug Common Issues

#### 1. PostgreSQL Connection Issues
```bash
# Check PostgreSQL pod status
kubectl get pods -l app=postgres -n finance-tracker

# Test database connectivity
kubectl exec -it postgres-0 -n finance-tracker -- psql -U financeuser -d financedb -c "SELECT version();"

# Check service resolution
kubectl exec -it deployment/finance-app -n finance-tracker -- nslookup postgres-service
```

#### 2. Redis Connection Issues
```bash
# Check Redis pod status
kubectl get pods -l app=redis -n finance-tracker

# Test Redis connectivity
kubectl exec -it deployment/redis -n finance-tracker -- redis-cli ping

# Check Redis service
kubectl exec -it deployment/finance-app -n finance-tracker -- nslookup redis-service
```

#### 3. Application Not Starting
```bash
# Check init container logs
kubectl logs deployment/finance-app -c wait-for-postgres -n finance-tracker

# Check application container logs
kubectl logs deployment/finance-app -c finance-app -n finance-tracker

# Describe deployment for events
kubectl describe deployment finance-app -n finance-tracker
```

#### 4. Storage Issues
```bash
# Check PVC status
kubectl get pvc -n finance-tracker

# Check storage class
kubectl get storageclass

# Describe PVC for events
kubectl describe pvc uploads-pvc -n finance-tracker
```

#### 5. Ingress Not Working
```bash
# Check ingress controller
kubectl get pods -n ingress-nginx

# Check ingress resource
kubectl describe ingress finance-app-ingress -n finance-tracker

# Test ingress controller
kubectl get svc -n ingress-nginx
```

## 🧪 Testing the Application

### 1. Health Check
```bash
# Test application health
curl $(minikube service finance-app-service -n finance-tracker --url)

# Expected: HTML response from Flask app
```

### 2. Database Connectivity
```bash
# Connect to database
kubectl exec -it postgres-0 -n finance-tracker -- psql -U financeuser -d financedb

# List tables (after first app run)
\dt

# Check user table
SELECT * FROM users;
```

### 3. Redis Connectivity
```bash
# Connect to Redis
kubectl exec -it deployment/redis -n finance-tracker -- redis-cli

# Test Redis commands
ping
set test "Hello Redis"
get test
```

### 4. File Upload Test
```bash
# Create test file
echo "Test receipt" > test-receipt.txt

# Test file upload via curl (replace URL with your service URL)
curl -X POST $(minikube service finance-app-service -n finance-tracker --url)/add_transaction \
  -F "amount=25.50" \
  -F "description=Test Transaction" \
  -F "transaction_type=expense" \
  -F "receipt=@test-receipt.txt"
```

## 📊 Performance Optimization

### Resource Limits
```yaml
# Current resource configuration
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### Scaling Application
```bash
# Scale application pods
kubectl scale deployment finance-app --replicas=3 -n finance-tracker

# Verify scaling
kubectl get pods -n finance-tracker
```

### Database Performance
```bash
# Monitor database performance
kubectl exec -it postgres-0 -n finance-tracker -- psql -U financeuser -d financedb -c "
SELECT 
    datname,
    numbackends,
    xact_commit,
    xact_rollback,
    blks_read,
    blks_hit
FROM pg_stat_database 
WHERE datname = 'financedb';"
```

## 🔒 Security Considerations

### 1. Secrets Management
- Secrets are base64 encoded (not encrypted)
- For production: Use external secret management (Vault, AWS Secrets Manager)
- Rotate secrets regularly

### 2. Network Security
```bash
# Create network policies (optional)
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: finance-app-netpol
  namespace: finance-tracker
spec:
  podSelector:
    matchLabels:
      app: finance-app
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 5000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
EOF
```

### 3. RBAC (Role-Based Access Control)
```bash
# Create service account with limited permissions
kubectl apply -f - <<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: finance-app-sa
  namespace: finance-tracker
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: finance-app-role
  namespace: finance-tracker
rules:
- apiGroups: [""]
  resources: ["pods", "services"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: finance-app-binding
  namespace: finance-tracker
subjects:
- kind: ServiceAccount
  name: finance-app-sa
  namespace: finance-tracker
roleRef:
  kind: Role
  name: finance-app-role
  apiGroup: rbac.authorization.k8s.io
EOF
```

## 🧹 Cleanup

### Remove Application
```bash
# Delete all resources in namespace
kubectl delete namespace finance-tracker

# Or delete individual resources
kubectl delete -f k8s/minikube/
```

### Stop Minikube
```bash
# Stop Minikube
minikube stop

# Delete Minikube cluster (removes all data)
minikube delete
```

## 📚 Additional Resources

### Useful Commands
```bash
# Minikube dashboard
minikube dashboard

# SSH into Minikube node
minikube ssh

# View Minikube logs
minikube logs

# Check addon status
minikube addons list

# Mount local directory
minikube mount /local/path:/minikube/path
```

### Kubernetes Resources
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Minikube Documentation](https://minikube.sigs.k8s.io/docs/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)

### Troubleshooting Resources
- [Kubernetes Troubleshooting Guide](https://kubernetes.io/docs/tasks/debug-application-cluster/)
- [Minikube Troubleshooting](https://minikube.sigs.k8s.io/docs/handbook/troubleshooting/)

## 🎯 Next Steps

1. **Production Deployment**: Migrate to managed Kubernetes (EKS, GKE, AKS)
2. **CI/CD Integration**: Setup automated deployments with GitHub Actions
3. **Monitoring**: Add Prometheus and Grafana for observability
4. **Backup Strategy**: Implement database and volume backups
5. **Security Hardening**: Add Pod Security Standards and network policies
6. **Performance Testing**: Load testing with tools like k6 or Artillery

---

**🎉 Congratulations!** You have successfully deployed the Personal Finance Tracker on Minikube with a complete understanding of each component and its purpose.
