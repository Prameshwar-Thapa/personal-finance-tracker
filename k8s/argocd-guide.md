# ArgoCD Complete Guide

## Table of Contents
1. [What is ArgoCD?](#what-is-argocd)
2. [Why Use ArgoCD?](#why-use-argocd)
3. [Core Concepts](#core-concepts)
4. [Step-by-Step Installation](#step-by-step-installation)
5. [Access ArgoCD Web UI](#access-argocd-web-ui)
6. [Creating Your First Application](#creating-your-first-application)
7. [GitOps Workflow](#gitops-workflow)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

## What is ArgoCD?

ArgoCD is a **declarative, GitOps continuous delivery tool** for Kubernetes. It follows the GitOps pattern of using Git repositories as the source of truth for defining the desired application state.

### Key Features
- **Declarative**: Application definitions, configurations, and environments are declarative and version controlled
- **Automated**: Automatically deploys the desired application state in the specified target environments
- **Auditable**: All changes are tracked in Git with full audit trail
- **Self-healing**: Automatically corrects drift between desired and actual state

## Why Use ArgoCD?

### Traditional Deployment Problems
```bash
# Traditional CI/CD (Push-based)
Developer → CI Pipeline → kubectl apply → Kubernetes Cluster
```
**Issues:**
- CI/CD system needs cluster access (security risk)
- No visibility into actual cluster state
- Manual intervention required for rollbacks
- Difficult to track what's deployed where

### ArgoCD Solution (Pull-based)
```bash
# GitOps with ArgoCD (Pull-based)
Developer → Git Repository → ArgoCD (running in cluster) → Kubernetes Resources
```
**Benefits:**
- **Security**: No external access to cluster needed
- **Visibility**: Real-time view of application state
- **Automation**: Self-healing and automatic sync
- **Auditability**: Complete deployment history in Git

## Core Concepts

### 1. Application
An ArgoCD Application represents a deployed application instance in your cluster.

### 2. Repository
Git repositories containing your Kubernetes manifests, Helm charts, or Kustomize configurations.

### 3. Sync Policy
Defines how ArgoCD synchronizes the desired state:
- **Manual**: Requires manual sync trigger
- **Automatic**: Syncs automatically on Git changes
- **Self-heal**: Corrects manual changes to cluster

### 4. Health Status
ArgoCD monitors resource health:
- **Healthy**: Resource is running as expected
- **Progressing**: Resource is being updated
- **Degraded**: Resource has issues
- **Missing**: Resource not found in cluster

## Step-by-Step Installation

### 1. Add the Argo CD Helm Repository

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
```

### 2. Create a Namespace for Argo CD

```bash
kubectl create namespace argocd
```

### 3. Install Argo CD using Helm

This will install the latest stable version of Argo CD into the argocd namespace:

```bash
helm install argocd argo/argo-cd -n argocd
```

If you want a specific version:
```bash
helm install argocd argo/argo-cd -n argocd --version <version>
```

### 4. Verify Installation

Check pods:
```bash
kubectl get pods -n argocd
```

You should see something like:
```
argocd-application-controller-xxxxxxx   1/1   Running
argocd-dex-server-xxxxxxx               1/1   Running
argocd-redis-xxxxxxx                    1/1   Running
argocd-repo-server-xxxxxxx              1/1   Running
argocd-server-xxxxxxx                   1/1   Running
```

### 5. Expose Argo CD (so you can access it in a browser)

#### Option 1: Change Service to NodePort (simple local test)

```bash
kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "NodePort"}}'
```

Get the port:
```bash
kubectl get svc argocd-server -n argocd
```

Use `http://<NodeIP>:<NodePort>` to access the UI.

#### Option 2: Use LoadBalancer (if on AWS, GCP, Azure)

```bash
kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "LoadBalancer"}}'
```

Check external IP / DNS:
```bash
kubectl get svc argocd-server -n argocd
```

Use the EXTERNAL-IP to access in browser.

### 6. Get the Initial Admin Password

The password is stored as a secret in your cluster:

```bash
kubectl get secret argocd-initial-admin-secret -n argocd -o jsonpath="{.data.password}" | base64 --decode; echo
```

Username is always `admin`.

## Access ArgoCD Web UI

### Method 1: Port Forward (Recommended for Local Testing)

```bash
# Port forward to access UI locally
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Access in browser: https://localhost:8080
# Username: admin
# Password: (from step 6 above)
```

### Method 2: LoadBalancer (For Cloud Deployments)

If you used LoadBalancer service type:
```bash
# Get the external URL
kubectl get svc argocd-server -n argocd

# Access using the EXTERNAL-IP in browser
# https://<EXTERNAL-IP>
```

### Method 3: NodePort (For Local Clusters)

If you used NodePort service type:
```bash
# Get the node port
kubectl get svc argocd-server -n argocd

# Access using: https://<NODE-IP>:<NODE-PORT>
```

### First Login Steps

1. **Open browser** and navigate to ArgoCD URL
2. **Accept SSL certificate** (if using self-signed)
3. **Login with**:
   - Username: `admin`
   - Password: (from installation step 6)
4. **Change default password** (recommended)

## Creating Your First Application

### 1. Prepare Your Git Repository

Ensure your personal finance tracker repository has Kubernetes manifests in a `k8s/` directory:

```
personal-finance-tracker/
├── k8s/
│   ├── namespace.yaml
│   ├── secrets.yaml
│   ├── configmap.yaml
│   ├── postgres-statefulset.yaml
│   ├── redis-deployment.yaml
│   ├── app-deployment.yaml
│   └── app-service.yaml
└── ... (other files)
```

### 2. Create Application via Web UI

1. **Click "NEW APP"** in ArgoCD UI
2. **Fill in details**:
   - **Application Name**: `personal-finance-tracker`
   - **Project**: `default`
   - **Sync Policy**: `Manual` (for now)
   
3. **Source Configuration**:
   - **Repository URL**: `https://github.com/your-username/personal-finance-tracker`
   - **Revision**: `HEAD`
   - **Path**: `k8s`
   
4. **Destination Configuration**:
   - **Cluster URL**: `https://kubernetes.default.svc`
   - **Namespace**: `finance-tracker`
   
5. **Click "CREATE"**

### 3. Create Application via YAML

Alternatively, create an application using YAML:

```yaml
# finance-tracker-app.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: personal-finance-tracker
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/your-username/personal-finance-tracker
    targetRevision: HEAD
    path: k8s
  destination:
    server: https://kubernetes.default.svc
    namespace: finance-tracker
  syncPolicy:
    automated:
      prune: true      # Remove resources not in Git
      selfHeal: true   # Correct manual changes
    syncOptions:
    - CreateNamespace=true
```

Apply it:
```bash
kubectl apply -f finance-tracker-app.yaml
```

### 4. Sync Your Application

1. **Click on your application** in ArgoCD UI
2. **Click "SYNC"** button
3. **Review changes** and click "SYNCHRONIZE"
4. **Monitor deployment** progress in real-time

## GitOps Workflow

### 1. Developer Workflow
```bash
# Developer makes changes to Kubernetes manifests
git add k8s/
git commit -m "Update deployment image to v1.2.0"
git push origin main
```

### 2. ArgoCD Detects Changes
```bash
# ArgoCD polls Git repository (default: 3 minutes)
# Detects manifest changes
# Shows "OutOfSync" status in UI
```

### 3. ArgoCD Syncs Changes
```bash
# If auto-sync enabled: Automatically applies changes
# If manual sync: Requires manual trigger via UI or CLI
# Updates Kubernetes resources
# Shows "Synced" and "Healthy" status
```

### 4. Monitor and Verify
- **Real-time status** in ArgoCD UI
- **Resource health** monitoring
- **Event logs** and history
- **Rollback capability** if needed

## Best Practices

### 1. Repository Structure
```
personal-finance-tracker/
├── k8s/
│   ├── base/                    # Base configurations
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── kustomization.yaml
│   └── overlays/               # Environment-specific
│       ├── dev/
│       ├── staging/
│       └── production/
└── argocd/
    └── applications/
        ├── finance-tracker-dev.yaml
        ├── finance-tracker-staging.yaml
        └── finance-tracker-prod.yaml
```

### 2. Security Best Practices
```bash
# Change default admin password
# (Do this via ArgoCD UI: User Info → Update Password)

# Delete initial admin secret after changing password
kubectl -n argocd delete secret argocd-initial-admin-secret

# Use private Git repositories for sensitive configurations
# Enable RBAC for team access
```

### 3. Sync Policies

#### Conservative Approach (Manual Sync)
```yaml
syncPolicy: {}  # Manual sync only
```

#### Automated with Safety
```yaml
syncPolicy:
  automated:
    prune: false     # Don't delete resources automatically
    selfHeal: false  # Don't correct manual changes
```

#### Fully Automated (Production Ready)
```yaml
syncPolicy:
  automated:
    prune: true      # Remove resources not in Git
    selfHeal: true   # Correct manual changes
  retry:
    limit: 3
    backoff:
      duration: 5s
      factor: 2
      maxDuration: 3m
```

### 4. Application Health Monitoring

ArgoCD automatically monitors:
- **Pod status** and readiness
- **Service endpoints**
- **Ingress health**
- **Custom resource status**

You can also define custom health checks for your applications.

## Troubleshooting

### Common Issues and Solutions

#### 1. Application Stuck in "Progressing"

**Symptoms:**
- Application shows "Progressing" status for extended time
- Pods not starting properly

**Solutions:**
```bash
# Check application details in UI or CLI
kubectl get pods -n finance-tracker

# Check pod logs
kubectl logs -n finance-tracker deployment/finance-app

# Check events
kubectl get events -n finance-tracker --sort-by='.lastTimestamp'

# Manual sync with force (if needed)
# Use ArgoCD UI: Click app → SYNC → Force sync
```

#### 2. "OutOfSync" Status

**Symptoms:**
- Application shows "OutOfSync" even after Git push
- Changes not being applied

**Solutions:**
```bash
# Check if auto-sync is enabled
# In ArgoCD UI: Check app details → Sync Policy

# Manual refresh and sync
# In ArgoCD UI: Click REFRESH → then SYNC

# Check repository access
# Ensure ArgoCD can access your Git repository
```

#### 3. Repository Access Issues

**Symptoms:**
- "Repository not accessible" errors
- Authentication failures

**Solutions:**
```bash
# For public repositories: Ensure URL is correct
# For private repositories: Add repository credentials in ArgoCD UI
# Settings → Repositories → Connect Repo

# Check repository URL format:
# HTTPS: https://github.com/username/repo
# SSH: git@github.com:username/repo.git
```

#### 4. Permission Issues

**Symptoms:**
- "Insufficient permissions" errors
- Resources not being created

**Solutions:**
```bash
# Check ArgoCD service account permissions
kubectl auth can-i '*' '*' --as=system:serviceaccount:argocd:argocd-application-controller

# Ensure target namespace exists or enable CreateNamespace
# In application YAML: syncOptions: - CreateNamespace=true
```

### Debugging Commands

```bash
# Check ArgoCD server logs
kubectl logs -n argocd deployment/argocd-server

# Check application controller logs
kubectl logs -n argocd deployment/argocd-application-controller

# Check repository server logs
kubectl logs -n argocd deployment/argocd-repo-server

# List all applications
kubectl get applications -n argocd

# Get application details
kubectl describe application personal-finance-tracker -n argocd
```

### Health Check Script

Create a simple health check script:

```bash
#!/bin/bash
# argocd-health-check.sh

echo "=== ArgoCD Health Check ==="

# 1. Check ArgoCD pods
echo "1. Checking ArgoCD pods..."
kubectl get pods -n argocd

# 2. Check ArgoCD service
echo "2. Checking ArgoCD service..."
kubectl get svc argocd-server -n argocd

# 3. Check applications
echo "3. Checking applications..."
kubectl get applications -n argocd

# 4. Test ArgoCD API (if port-forward is running)
echo "4. Testing ArgoCD API..."
if curl -k -s https://localhost:8080/api/version > /dev/null 2>&1; then
    echo "✅ ArgoCD API is accessible"
else
    echo "❌ ArgoCD API is not accessible (check port-forward)"
fi

echo "=== Health Check Complete ==="
```

Make it executable and run:
```bash
chmod +x argocd-health-check.sh
./argocd-health-check.sh
```

## Key Benefits for Personal Finance Tracker

✅ **Automated Deployments**: Push to Git → Automatic deployment  
✅ **Version Control**: All deployment history tracked in Git  
✅ **Self-Healing**: Automatically corrects manual changes  
✅ **Rollback Capability**: Easy rollback to previous versions  
✅ **Multi-Environment**: Manage dev, staging, production from one place  
✅ **Security**: No external cluster access needed  
✅ **Visibility**: Real-time view of application state  

## Next Steps

1. **Set up your Git repository** with Kubernetes manifests
2. **Install ArgoCD** using the steps above
3. **Create your first application** for the personal finance tracker
4. **Enable auto-sync** once you're comfortable with the workflow
5. **Explore advanced features** like ApplicationSets and Projects

This simplified guide gets you started with ArgoCD quickly without overwhelming complexity, while still providing the essential knowledge for production use!
