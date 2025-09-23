# Complete EKS Deployment Guide for Personal Finance Tracker

## 🎯 **What You'll Learn**

This comprehensive guide will teach you how to deploy a production-ready Personal Finance Tracker application on Amazon EKS (Elastic Kubernetes Service). You'll understand not just the "how" but the "why" behind each component and decision.

## 🏗️ **Architecture Overview**

By the end of this guide, you'll have deployed this architecture:

```
┌─────────────────────────────────────────────────────────────────┐
│                        AWS EKS Cluster                         │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Finance App   │  │   PostgreSQL    │  │      Redis      │ │
│  │   (2 replicas)  │  │   (Database)    │  │    (Cache)      │ │
│  │                 │  │                 │  │                 │ │
│  │ ┌─────────────┐ │  │ ┌─────────────┐ │  │ ┌─────────────┐ │ │
│  │ │    Pod 1    │ │  │ │  Postgres   │ │  │ │    Redis    │ │ │
│  │ │ Flask:5000  │ │  │ │   :5432     │ │  │ │    :6379    │ │ │
│  │ └─────────────┘ │  │ └─────────────┘ │  │ └─────────────┘ │ │
│  │ ┌─────────────┐ │  │                 │  │                 │ │
│  │ │    Pod 2    │ │  │ ┌─────────────┐ │  │ ┌─────────────┐ │ │
│  │ │ Flask:5000  │ │  │ │  EBS Vol    │ │  │ │  EBS Vol    │ │ │
│  │ └─────────────┘ │  │ │   20Gi      │ │  │ │    5Gi      │ │ │
│  │                 │  │ └─────────────┘ │  │ └─────────────┘ │ │
│  │ ┌─────────────┐ │  └─────────────────┘  └─────────────────┘ │
│  │ │  EBS Vol    │ │                                           │
│  │ │   10Gi      │ │  ┌─────────────────────────────────────┐ │
│  │ │ (Uploads)   │ │  │            Services                 │ │
│  │ └─────────────┘ │  │                                     │ │
│  └─────────────────┘  │ • finance-app-service:80            │ │
│                       │ • postgres-service:5432             │ │
│                       │ • redis-service:6379                │ │
│                       └─────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 📚 **Table of Contents**
1. [Understanding Kubernetes Components](#understanding-kubernetes-components)
2. [Prerequisites & Environment Setup](#prerequisites--environment-setup)
3. [EKS Cluster Creation](#eks-cluster-creation)
4. [OIDC Provider & Service Accounts Setup](#oidc-provider--service-accounts-setup)
5. [EBS CSI Driver Installation](#ebs-csi-driver-installation)
6. [Storage Configuration](#storage-configuration)
7. [Application Components Deployment](#application-components-deployment)
8. [Service Configuration](#service-configuration)
9. [Load Balancer & Ingress Setup](#load-balancer--ingress-setup)
10. [Monitoring & Logging](#monitoring--logging)
11. [Security Best Practices](#security-best-practices)
12. [Troubleshooting Guide](#troubleshooting-guide)
13. [Production Considerations](#production-considerations)

---

## Understanding Kubernetes Components

Before diving into deployment, let's understand the key Kubernetes components we'll use and why each is important for our finance application.

### 🏗️ **Core Kubernetes Objects**

#### **1. Pods - The Smallest Deployable Unit**

**What it is**: A Pod is the smallest deployable unit in Kubernetes, containing one or more containers that share storage and network.

**Why we need it**: 
- Our Flask application runs inside a Pod
- Each Pod gets its own IP address
- Pods are ephemeral - they can be created, destroyed, and recreated

**In our finance app**:
```yaml
# A Pod contains our Flask application
Pod:
  - Container: finance-app (Flask + Gunicorn)
  - Volume: uploads-storage (for receipt files)
  - Network: Shared IP for all containers in the pod
```

#### **2. Deployments - Managing Pod Replicas**

**What it is**: A Deployment manages a set of identical Pods, ensuring the desired number are always running.

**Why we need it**:
- **High Availability**: If one Pod crashes, Deployment creates a new one
- **Scaling**: Easy to scale from 1 to 10 replicas
- **Rolling Updates**: Update application without downtime
- **Rollback**: Easily revert to previous version if issues occur

**In our finance app**:
```yaml
Deployment: finance-app
  replicas: 2  # Always keep 2 Pods running
  strategy: RollingUpdate  # Update one Pod at a time
  template:
    spec:
      containers:
      - name: finance-app
        image: your-app:latest
```

#### **3. Services - Network Access to Pods**

**What it is**: A Service provides a stable network endpoint to access a set of Pods.

**Why we need it**:
- **Stable IP**: Pods have changing IPs, Services provide stable ones
- **Load Balancing**: Distributes traffic across multiple Pod replicas
- **Service Discovery**: Other components can find your app by service name
- **Port Abstraction**: External port can differ from container port

**Service Types**:
- **ClusterIP**: Internal access only (default)
- **NodePort**: External access via node IPs
- **LoadBalancer**: Cloud provider load balancer
- **Headless**: Direct Pod access without load balancing

#### **4. StatefulSets - For Stateful Applications**

**What it is**: Like Deployments, but for applications that need persistent identity and storage.

**Why we use it for PostgreSQL**:
- **Stable Network Identity**: postgres-0, postgres-1, etc.
- **Ordered Deployment**: Pods start in sequence
- **Persistent Storage**: Each Pod gets its own persistent volume
- **Graceful Scaling**: Controlled scaling up/down

#### **5. ConfigMaps and Secrets - Configuration Management**

**ConfigMaps** store non-sensitive configuration:
```yaml
ConfigMap:
  DATABASE_URL: "postgresql://user@host:5432/db"
  FLASK_ENV: "production"
  UPLOAD_FOLDER: "/app/uploads"
```

**Secrets** store sensitive data (base64 encoded):
```yaml
Secret:
  SECRET_KEY: "your-secret-key"
  POSTGRES_PASSWORD: "secure-password"
```

**Why separate them**:
- **Security**: Secrets can have restricted access
- **Flexibility**: Change config without rebuilding images
- **Environment Promotion**: Same image, different configs

#### **6. Persistent Volumes (PV) and Claims (PVC)**

**What they are**:
- **PV**: Actual storage resource (EBS volume, NFS, etc.)
- **PVC**: Request for storage by a Pod

**Why we need them**:
- **Data Persistence**: Data survives Pod restarts
- **Storage Abstraction**: Pods request storage without knowing details
- **Dynamic Provisioning**: Storage created automatically when needed

**In our finance app**:
```yaml
PVC: postgres-pvc (20Gi) → Database data
PVC: uploads-pvc (10Gi)  → Receipt files
PVC: redis-pvc (5Gi)     → Redis persistence
```

### 🔐 **Security Components**

#### **Service Accounts - Pod Identity**

**What it is**: An identity for Pods to interact with Kubernetes API and AWS services.

**Why we need it**:
- **AWS Integration**: Access AWS services securely
- **RBAC**: Control what Pods can do in the cluster
- **Audit**: Track which Pod performed which action

#### **RBAC (Role-Based Access Control)**

**What it is**: System to control who can do what in your cluster.

**Components**:
- **Role**: Permissions within a namespace
- **ClusterRole**: Cluster-wide permissions
- **RoleBinding**: Assigns Role to users/service accounts
- **ClusterRoleBinding**: Assigns ClusterRole cluster-wide

### 🌐 **Networking Components**

#### **Ingress - HTTP/HTTPS Routing**

**What it is**: Manages external access to services via HTTP/HTTPS.

**Why use it instead of LoadBalancer**:
- **Cost Effective**: One load balancer for multiple services
- **SSL Termination**: Handle HTTPS certificates
- **Path-based Routing**: Route /api to API service, /web to web service
- **Host-based Routing**: Route different domains to different services

#### **Network Policies - Traffic Control**

**What they are**: Firewall rules for Pod-to-Pod communication.

**Why we need them**:
- **Security**: Prevent unauthorized access between Pods
- **Compliance**: Meet security requirements
- **Isolation**: Separate different application tiers

### 📊 **Monitoring Components**

#### **Probes - Health Checks**

**Liveness Probe**: Is the container healthy?
- If fails → Kubernetes restarts the container

**Readiness Probe**: Is the container ready to serve traffic?
- If fails → Kubernetes stops sending traffic

**Startup Probe**: Has the container started successfully?
- For slow-starting applications

### 🎯 **Why This Architecture for Finance App**

Our Personal Finance Tracker needs:

1. **High Availability**: 2 app replicas ensure service continues if one fails
2. **Data Persistence**: PostgreSQL StatefulSet with persistent storage
3. **Performance**: Redis caching for faster response times
4. **Security**: Secrets for sensitive data, service accounts for AWS access
5. **Scalability**: Easy to scale app replicas based on load
6. **Maintainability**: Separate concerns (app, database, cache)
7. **Monitoring**: Health checks ensure system reliability

---
## Prerequisites & Environment Setup

### 🛠️ **Required Tools Installation**

#### **1. AWS CLI v2 - AWS Command Line Interface**

**What it is**: Command-line tool to interact with AWS services.

**Why we need it**: 
- Create and manage EKS clusters
- Configure IAM roles and policies
- Manage AWS resources from command line

**Installation**:
```bash
# Download and install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Verify installation
aws --version
# Expected output: aws-cli/2.x.x Python/3.x.x Linux/x.x.x exe/x86_64.x
```

**Configuration**:
```bash
# Configure AWS CLI with your credentials
aws configure
# Enter:
# - AWS Access Key ID: Your access key
# - AWS Secret Access Key: Your secret key  
# - Default region name: us-east-1 (or your preferred region)
# - Default output format: json

# Test your configuration
aws sts get-caller-identity
# Should return your account ID, user ARN, and user ID
```

#### **2. kubectl - Kubernetes Command Line Tool**

**What it is**: Command-line tool to interact with Kubernetes clusters.

**Why we need it**:
- Deploy applications to Kubernetes
- Manage cluster resources
- Debug and troubleshoot issues
- View logs and cluster status

**Installation**:
```bash
# Download kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"

# Install kubectl
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Verify installation
kubectl version --client
# Should show client version information
```

#### **3. eksctl - EKS Management Tool**

**What it is**: Official CLI tool for creating and managing EKS clusters.

**Why we need it**:
- Simplifies EKS cluster creation
- Manages node groups automatically
- Handles IAM roles and policies
- Configures OIDC providers

**Installation**:
```bash
# Download and install eksctl
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# Verify installation
eksctl version
# Should show eksctl version
```

#### **4. Helm - Kubernetes Package Manager**

**What it is**: Package manager for Kubernetes applications.

**Why we need it**:
- Install complex applications easily
- Manage application dependencies
- Template Kubernetes manifests
- Install AWS Load Balancer Controller

**Installation**:
```bash
# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Verify installation
helm version
# Should show Helm version
```

### 🌍 **Environment Variables Setup**

**Why we need environment variables**:
- Consistency across commands
- Avoid repetitive typing
- Easy to change values in one place
- Reduce human errors

```bash
# Set up environment variables for your deployment
export AWS_REGION=us-east-1
export CLUSTER_NAME=finance-tracker-cluster
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export NAMESPACE=finance-app

# Make them persistent across terminal sessions
cat <<EOF >> ~/.bashrc
export AWS_REGION=us-east-1
export CLUSTER_NAME=finance-tracker-cluster
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export NAMESPACE=finance-app
EOF

# Reload your bash configuration
source ~/.bashrc

# Verify environment variables
echo "AWS Region: $AWS_REGION"
echo "Cluster Name: $CLUSTER_NAME"
echo "AWS Account ID: $AWS_ACCOUNT_ID"
echo "Namespace: $NAMESPACE"
```

### 🔐 **AWS Permissions Required**

**Why proper permissions matter**:
- Security: Follow principle of least privilege
- Functionality: Ensure all operations work
- Compliance: Meet organizational requirements

**Required IAM permissions for your AWS user**:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "eks:*",
                "ec2:*",
                "iam:*",
                "cloudformation:*",
                "autoscaling:*",
                "elasticloadbalancing:*"
            ],
            "Resource": "*"
        }
    ]
}
```

**Note**: In production, use more restrictive permissions.

---
## EKS Cluster Creation

### 🎯 **Understanding EKS Cluster Components**

**What is EKS**:
- **Managed Kubernetes**: AWS manages the control plane
- **High Availability**: Control plane runs across multiple AZs
- **Security**: Integrated with AWS IAM and VPC
- **Scalability**: Auto-scaling node groups

**EKS Cluster Components**:
```
┌─────────────────────────────────────────────────────────┐
│                    EKS Cluster                         │
│                                                         │
│  ┌─────────────────┐    ┌─────────────────────────────┐ │
│  │  Control Plane  │    │        Worker Nodes         │ │
│  │   (Managed)     │    │      (Your EC2s)            │ │
│  │                 │    │                             │ │
│  │ • API Server    │    │ ┌─────────┐ ┌─────────────┐ │ │
│  │ • etcd          │◄──►│ │ Node 1  │ │   Node 2    │ │ │
│  │ • Scheduler     │    │ │ t3.med  │ │   t3.med    │ │ │
│  │ • Controller    │    │ └─────────┘ └─────────────┘ │ │
│  └─────────────────┘    └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 📝 **Step 1: Create Cluster Configuration File**

**Why use a configuration file**:
- **Reproducible**: Same cluster every time
- **Version Control**: Track changes over time
- **Documentation**: Self-documenting infrastructure
- **Complex Configurations**: Handle advanced settings

```bash
# Create cluster configuration file
cat <<EOF > cluster-config.yaml
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: ${CLUSTER_NAME}
  region: ${AWS_REGION}
  version: "1.28"  # Kubernetes version

# Enable logging for better observability
cloudWatch:
  clusterLogging:
    enableTypes: ["api", "audit", "authenticator", "controllerManager", "scheduler"]
    # api: API server logs
    # audit: Audit logs for security
    # authenticator: Authentication logs
    # controllerManager: Controller manager logs
    # scheduler: Scheduler logs

# IAM configuration for OIDC (OpenID Connect)
iam:
  withOIDC: true  # Enables OIDC provider for service accounts

# Node groups configuration
nodeGroups:
  - name: worker-nodes
    instanceType: t3.medium  # 2 vCPU, 4GB RAM - good for our workload
    desiredCapacity: 2       # Start with 2 nodes
    minSize: 1              # Minimum 1 node
    maxSize: 4              # Maximum 4 nodes for auto-scaling
    volumeSize: 20          # 20GB EBS volume per node
    volumeType: gp3         # GP3 for better price/performance
    
    # Enable Systems Manager for node management
    ssh:
      enableSsm: true  # Allows SSH via AWS Systems Manager
    
    # IAM policies for worker nodes
    iam:
      attachPolicyARNs:
        - arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy
        - arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy
        - arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly
        - arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy

# Add-ons configuration (optional but recommended)
addons:
  - name: vpc-cni      # Container Network Interface
    version: latest
  - name: coredns      # DNS resolution
    version: latest
  - name: kube-proxy   # Network proxy
    version: latest
  - name: aws-ebs-csi-driver  # EBS storage driver
    version: latest
    serviceAccountRoleARN: arn:aws:iam::${AWS_ACCOUNT_ID}:role/AmazonEKS_EBS_CSI_DriverRole

EOF
```

**Configuration Explanation**:

- **instanceType: t3.medium**: 
  - 2 vCPUs, 4GB RAM
  - Good balance of cost and performance
  - Suitable for our finance app workload

- **desiredCapacity: 2**: 
  - Start with 2 nodes for high availability
  - Can handle one node failure

- **volumeType: gp3**: 
  - Latest generation EBS volume
  - Better price/performance than gp2
  - 3,000 IOPS baseline

- **withOIDC: true**: 
  - Enables service accounts to assume IAM roles
  - Required for EBS CSI driver
  - Secure way to access AWS services

### 🚀 **Step 2: Create the EKS Cluster**

```bash
# Create the cluster (this takes 15-20 minutes)
echo "🚀 Creating EKS cluster... This will take 15-20 minutes"
eksctl create cluster -f cluster-config.yaml

# The process will:
# 1. Create VPC and subnets
# 2. Create EKS control plane
# 3. Create node group with EC2 instances
# 4. Configure networking and security groups
# 5. Install add-ons
# 6. Update your kubeconfig
```

**What happens during cluster creation**:
1. **VPC Creation**: New VPC with public/private subnets
2. **Control Plane**: EKS control plane in AWS-managed account
3. **Node Group**: EC2 instances join the cluster
4. **Networking**: Security groups and routing configured
5. **Add-ons**: Essential cluster components installed

### ✅ **Step 3: Verify Cluster Creation**

```bash
# Check cluster status
eksctl get cluster --region $AWS_REGION
# Should show your cluster as ACTIVE

# Verify kubectl configuration
kubectl config current-context
# Should show your EKS cluster context

# Check cluster info
kubectl cluster-info
# Should show API server and CoreDNS endpoints

# Check nodes
kubectl get nodes
# Should show 2 nodes in Ready state

# Check system pods
kubectl get pods -n kube-system
# Should show all system pods running

# Check node details
kubectl get nodes -o wide
# Shows node IPs, OS, kernel version, container runtime
```

**Expected output for `kubectl get nodes`**:
```
NAME                            STATUS   ROLES    AGE   VERSION
ip-192-168-1-100.ec2.internal   Ready    <none>   5m    v1.28.x-eks-xxxxx
ip-192-168-2-200.ec2.internal   Ready    <none>   5m    v1.28.x-eks-xxxxx
```

### 🔧 **Step 4: Update kubeconfig (if needed)**

```bash
# If kubectl doesn't work, update kubeconfig manually
aws eks update-kubeconfig --region $AWS_REGION --name $CLUSTER_NAME

# Verify the update
kubectl config get-contexts
# Should show your EKS cluster context with a star (*)
```

### 💰 **Cost Considerations**

**EKS Cluster Costs**:
- **Control Plane**: $0.10/hour (~$73/month)
- **Worker Nodes**: 2 × t3.medium = ~$60/month
- **EBS Volumes**: 2 × 20GB = ~$4/month
- **Data Transfer**: Variable based on usage

**Total estimated cost**: ~$137/month

**Cost Optimization Tips**:
- Use Spot instances for non-production
- Right-size your instances based on actual usage
- Use cluster autoscaler to scale down during low usage
- Monitor costs with AWS Cost Explorer

---
## OIDC Provider & Service Accounts Setup

### 🔐 **Understanding OIDC and Service Accounts**

**What is OIDC (OpenID Connect)**:
- **Identity Protocol**: Allows Kubernetes service accounts to assume AWS IAM roles
- **Secure**: No need to store AWS credentials in pods
- **Fine-grained**: Different service accounts can have different permissions
- **Auditable**: All AWS API calls are logged with the service account identity

**How it works**:
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Kubernetes    │    │   OIDC Provider │    │   AWS IAM       │
│   Service       │───►│   (EKS)         │───►│   Role          │
│   Account       │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                                              │
        └──────────────────────────────────────────────┘
                    Secure Token Exchange
```

**Why we need this**:
- **EBS CSI Driver**: Needs permissions to create/attach EBS volumes
- **Application**: May need to access S3, RDS, or other AWS services
- **Security**: Better than storing AWS keys in containers

### 🔍 **Step 1: Verify OIDC Provider**

The OIDC provider was automatically created by eksctl, but let's verify:

```bash
# Get OIDC issuer URL
OIDC_ISSUER=$(aws eks describe-cluster --name $CLUSTER_NAME --query "cluster.identity.oidc.issuer" --output text)
echo "OIDC Issuer: $OIDC_ISSUER"

# Verify OIDC provider exists in IAM
aws iam list-open-id-connect-providers | grep $(echo $OIDC_ISSUER | cut -d '/' -f 3,4,5)

# If the above command returns a result, OIDC is properly configured
```

**What this shows**:
- OIDC issuer URL (unique to your cluster)
- OIDC provider registered in AWS IAM
- Ready for service account integration

### 🛠️ **Step 2: Create IAM Role for EBS CSI Driver**

**Why EBS CSI Driver needs IAM permissions**:
- Create EBS volumes dynamically
- Attach volumes to EC2 instances
- Create snapshots for backups
- Tag volumes for organization

```bash
# Create trust policy for EBS CSI driver
cat <<EOF > ebs-csi-trust-policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::${AWS_ACCOUNT_ID}:oidc-provider/$(echo $OIDC_ISSUER | cut -d '/' -f 3-)"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "$(echo $OIDC_ISSUER | cut -d '/' -f 3-):sub": "system:serviceaccount:kube-system:ebs-csi-controller-sa",
          "$(echo $OIDC_ISSUER | cut -d '/' -f 3-):aud": "sts.amazonaws.com"
        }
      }
    }
  ]
}
EOF

# Create IAM role for EBS CSI driver
aws iam create-role \
  --role-name AmazonEKS_EBS_CSI_DriverRole \
  --assume-role-policy-document file://ebs-csi-trust-policy.json

# Attach the required policy
aws iam attach-role-policy \
  --role-name AmazonEKS_EBS_CSI_DriverRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy

# Verify role creation
aws iam get-role --role-name AmazonEKS_EBS_CSI_DriverRole
```

**Trust Policy Explanation**:
- **Principal**: Specifies the OIDC provider can assume this role
- **Condition**: Only allows specific service account to assume the role
- **StringEquals**: Ensures only the EBS CSI controller service account can use this role

### 👤 **Step 3: Create Service Account for Finance Application**

**Why our application needs a service account**:
- Future AWS integrations (S3 for file storage, SES for emails)
- Secure access without hardcoded credentials
- Audit trail of AWS API calls
- Fine-grained permissions

```bash
# Create service account for our finance app
cat <<EOF > finance-app-service-account.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: finance-app-sa
  namespace: $NAMESPACE
  labels:
    app: finance-app
    component: security
  annotations:
    # Future: Add IAM role ARN when needed
    # eks.amazonaws.com/role-arn: arn:aws:iam::${AWS_ACCOUNT_ID}:role/FinanceAppRole
EOF
```

**Optional: Create IAM Role for Finance App** (for future AWS service access):

```bash
# Create trust policy for finance app (optional - only if you need AWS services)
cat <<EOF > finance-app-trust-policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::${AWS_ACCOUNT_ID}:oidc-provider/$(echo $OIDC_ISSUER | cut -d '/' -f 3-)"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "$(echo $OIDC_ISSUER | cut -d '/' -f 3-):sub": "system:serviceaccount:$NAMESPACE:finance-app-sa",
          "$(echo $OIDC_ISSUER | cut -d '/' -f 3-):aud": "sts.amazonaws.com"
        }
      }
    }
  ]
}
EOF

# Create the role (optional - only if your app needs AWS services)
aws iam create-role \
  --role-name FinanceAppRole \
  --assume-role-policy-document file://finance-app-trust-policy.json

# Example: Add S3 access for file storage (optional)
# aws iam attach-role-policy \
#   --role-name FinanceAppRole \
#   --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess

# If you created the role, update the service account
# sed -i 's|# eks.amazonaws.com/role-arn:|eks.amazonaws.com/role-arn:|' finance-app-service-account.yaml
```

### ✅ **Step 4: Verify OIDC Configuration**

```bash
# Check if OIDC provider is working
kubectl get serviceaccounts -n kube-system | grep ebs-csi

# Should show ebs-csi-controller-sa service account

# Check OIDC provider details
aws iam get-open-id-connect-provider \
  --open-id-connect-provider-arn arn:aws:iam::${AWS_ACCOUNT_ID}:oidc-provider/$(echo $OIDC_ISSUER | cut -d '/' -f 3-)

# Should show thumbprints and client ID list
```

### 🔧 **Troubleshooting OIDC Issues**

**Common Issues**:

1. **OIDC Provider Not Found**:
```bash
# Create OIDC provider manually if missing
eksctl utils associate-iam-oidc-provider --cluster $CLUSTER_NAME --approve
```

2. **Service Account Can't Assume Role**:
```bash
# Check trust policy conditions
aws iam get-role --role-name AmazonEKS_EBS_CSI_DriverRole --query 'Role.AssumeRolePolicyDocument'

# Verify service account annotations
kubectl describe serviceaccount ebs-csi-controller-sa -n kube-system
```

3. **Permissions Denied**:
```bash
# Check attached policies
aws iam list-attached-role-policies --role-name AmazonEKS_EBS_CSI_DriverRole

# Check policy permissions
aws iam get-policy-version \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy \
  --version-id v1
```

### 📋 **OIDC Best Practices**

1. **Principle of Least Privilege**: Only grant necessary permissions
2. **Separate Roles**: Different service accounts for different purposes
3. **Regular Audits**: Review and rotate permissions regularly
4. **Monitoring**: Monitor AWS CloudTrail for service account usage
5. **Documentation**: Document which service accounts need which permissions

---
## EBS CSI Driver Installation

### 💾 **Understanding EBS CSI Driver**

**What is CSI (Container Storage Interface)**:
- **Standard Interface**: Kubernetes standard for storage plugins
- **Dynamic Provisioning**: Automatically creates storage when needed
- **Lifecycle Management**: Handles creation, attachment, mounting, and deletion
- **Vendor Agnostic**: Same interface for different storage providers

**Why EBS CSI Driver**:
- **Persistent Storage**: Data survives pod restarts and rescheduling
- **Performance**: High IOPS and throughput for database workloads
- **Reliability**: EBS volumes are replicated within AZ
- **Snapshots**: Built-in backup and restore capabilities
- **Encryption**: Data encryption at rest

**EBS CSI Driver Architecture**:
```
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                      │
│                                                             │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │  EBS CSI        │    │         Worker Nodes            │ │
│  │  Controller     │    │                                 │ │
│  │                 │    │ ┌─────────────┐ ┌─────────────┐ │ │
│  │ • Provisioner   │◄──►│ │ CSI Node    │ │ CSI Node    │ │ │
│  │ • Attacher      │    │ │ Plugin      │ │ Plugin      │ │ │
│  │ • Snapshotter   │    │ └─────────────┘ └─────────────┘ │ │
│  │ • Resizer       │    │        │               │        │ │
│  └─────────────────┘    └────────┼───────────────┼────────┘ │
│           │                      │               │          │
│           └──────────────────────┼───────────────┼──────────┘
│                                  ▼               ▼
│  ┌─────────────────────────────────────────────────────────┐
│  │                  AWS EBS Service                        │
│  │  ┌─────────────┐              ┌─────────────┐          │
│  │  │ EBS Volume  │              │ EBS Volume  │          │
│  │  │   (20Gi)    │              │   (10Gi)    │          │
│  │  └─────────────┘              └─────────────┘          │
│  └─────────────────────────────────────────────────────────┘
└─────────────────────────────────────────────────────────────┘
```

### 🔧 **Step 1: Install EBS CSI Driver Add-on**

**Why use EKS Add-on instead of manual installation**:
- **Managed**: AWS manages updates and security patches
- **Integrated**: Better integration with EKS
- **Reliable**: Tested and validated by AWS
- **Support**: AWS provides support for add-ons

```bash
# Install EBS CSI driver add-on
echo "🔧 Installing EBS CSI driver add-on..."
eksctl create addon \
  --name aws-ebs-csi-driver \
  --cluster $CLUSTER_NAME \
  --service-account-role-arn arn:aws:iam::${AWS_ACCOUNT_ID}:role/AmazonEKS_EBS_CSI_DriverRole \
  --force

# The --force flag updates the add-on if it already exists
```

**What this command does**:
1. Installs EBS CSI driver pods in kube-system namespace
2. Creates necessary RBAC permissions
3. Associates IAM role with service account
4. Configures driver to work with your cluster

### ✅ **Step 2: Verify EBS CSI Driver Installation**

```bash
# Check EBS CSI driver pods
kubectl get pods -n kube-system | grep ebs-csi
# Expected output:
# ebs-csi-controller-xxx   6/6     Running   0          2m
# ebs-csi-controller-xxx   6/6     Running   0          2m
# ebs-csi-node-xxx         3/3     Running   0          2m
# ebs-csi-node-xxx         3/3     Running   0          2m

# Check CSI driver registration
kubectl get csidriver
# Expected output:
# NAME              ATTACHREQUIRED   PODINFOONMOUNT   STORAGECAPACITY   TOKENREQUESTS   REQUIRESREPUBLISH   MODES        AGE
# ebs.csi.aws.com   true             false            false             <unset>         false               Persistent   2m

# Check CSI node info
kubectl get csinodes
# Should show your worker nodes with EBS CSI driver
```

**Understanding the pods**:
- **ebs-csi-controller**: Handles volume provisioning, attachment, snapshots
- **ebs-csi-node**: Runs on each node, handles volume mounting

### 🗄️ **Step 3: Create Storage Class**

**What is a Storage Class**:
- **Template**: Defines how storage should be provisioned
- **Parameters**: Specifies volume type, IOPS, encryption, etc.
- **Dynamic Provisioning**: Automatically creates PVs when PVCs are created
- **Default**: Can be set as default for the cluster

```bash
# Create EBS storage class with optimal settings
cat <<EOF > ebs-storage-class.yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ebs-gp3
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"  # Make this the default
provisioner: ebs.csi.aws.com  # Use EBS CSI driver
parameters:
  type: gp3                    # GP3 for better price/performance than GP2
  iops: "3000"                 # Baseline IOPS (can burst to 16,000)
  throughput: "125"            # MB/s throughput
  encrypted: "true"            # Encryption at rest (required for financial data)
  fsType: ext4                 # File system type
  # Optional: Add tags to EBS volumes
  tagSpecification_1: "Name=finance-tracker-volume"
  tagSpecification_2: "Environment=production"
  tagSpecification_3: "Application=finance-tracker"
volumeBindingMode: WaitForFirstConsumer  # Create volume in same AZ as pod
allowVolumeExpansion: true     # Allow volume resizing
reclaimPolicy: Delete          # Delete volume when PVC is deleted
EOF

# Apply storage class
kubectl apply -f ebs-storage-class.yaml

# Verify storage class
kubectl get storageclass
# Should show ebs-gp3 as default (marked with "(default)")
```

**Storage Class Parameters Explained**:

- **type: gp3**: 
  - Latest generation EBS volume
  - Better price/performance than gp2
  - Baseline 3,000 IOPS regardless of size

- **encrypted: "true"**: 
  - Data encrypted at rest
  - Required for financial applications
  - Uses AWS managed keys by default

- **volumeBindingMode: WaitForFirstConsumer**: 
  - Volume created in same AZ as pod
  - Prevents cross-AZ mounting issues
  - More efficient resource usage

- **allowVolumeExpansion: true**: 
  - Can increase volume size without downtime
  - Important for growing databases

### 🧪 **Step 4: Test EBS CSI Driver**

**Why test before deploying applications**:
- Verify permissions are correct
- Ensure storage class works
- Validate volume creation and mounting
- Catch issues early

```bash
# Create test PVC
cat <<EOF > test-ebs-pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: test-ebs-pvc
  namespace: default
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: ebs-gp3
  resources:
    requests:
      storage: 5Gi
EOF

# Create test pod
cat <<EOF > test-ebs-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: test-ebs-pod
  namespace: default
spec:
  containers:
  - name: test-container
    image: nginx:alpine
    volumeMounts:
    - name: test-volume
      mountPath: /data
    command: ["/bin/sh"]
    args: ["-c", "echo 'Testing EBS volume' > /data/test.txt && tail -f /dev/null"]
  volumes:
  - name: test-volume
    persistentVolumeClaim:
      claimName: test-ebs-pvc
EOF

# Apply test resources
kubectl apply -f test-ebs-pvc.yaml
kubectl apply -f test-ebs-pod.yaml

# Check PVC status (should be Bound)
kubectl get pvc test-ebs-pvc
# Expected: STATUS should be "Bound"

# Check pod status (should be Running)
kubectl get pod test-ebs-pod
# Expected: STATUS should be "Running"

# Verify file was created
kubectl exec test-ebs-pod -- cat /data/test.txt
# Expected output: "Testing EBS volume"

# Check the actual EBS volume created
kubectl describe pv $(kubectl get pvc test-ebs-pvc -o jsonpath='{.spec.volumeName}')
# Should show EBS volume ID and details
```

### 🧹 **Step 5: Clean Up Test Resources**

```bash
# Clean up test resources
kubectl delete pod test-ebs-pod
kubectl delete pvc test-ebs-pvc

# Verify cleanup
kubectl get pvc test-ebs-pvc
# Should show "No resources found"
```

### 🔍 **Troubleshooting EBS CSI Driver**

**Common Issues and Solutions**:

1. **PVC Stuck in Pending**:
```bash
# Check EBS CSI controller logs
kubectl logs -n kube-system -l app=ebs-csi-controller

# Common causes:
# - IAM permissions missing
# - Storage class not found
# - Node in different AZ than volume
```

2. **Pod Can't Mount Volume**:
```bash
# Check EBS CSI node logs
kubectl logs -n kube-system -l app=ebs-csi-node

# Check pod events
kubectl describe pod <pod-name>

# Common causes:
# - Volume not attached to node
# - File system corruption
# - Mount point issues
```

3. **Permission Denied Errors**:
```bash
# Verify IAM role has correct policies
aws iam list-attached-role-policies --role-name AmazonEKS_EBS_CSI_DriverRole

# Check service account annotation
kubectl describe serviceaccount ebs-csi-controller-sa -n kube-system
```

### 📊 **EBS Volume Types Comparison**

| Volume Type | Use Case | IOPS | Throughput | Cost |
|-------------|----------|------|------------|------|
| **gp3** | General purpose, our choice | 3,000-16,000 | 125-1,000 MB/s | Low |
| **gp2** | Legacy general purpose | 3-10,000 | Up to 250 MB/s | Low |
| **io1/io2** | High IOPS databases | Up to 64,000 | Up to 1,000 MB/s | High |
| **st1** | Big data, data warehouses | N/A | Up to 500 MB/s | Very Low |
| **sc1** | Cold storage | N/A | Up to 250 MB/s | Lowest |

**Why we chose gp3**:
- Best price/performance ratio
- Sufficient IOPS for our workload
- Can scale IOPS independently of size
- Good for both database and file storage

---
## Storage Configuration

### 📦 **Understanding Persistent Storage in Kubernetes**

**Why Persistent Storage Matters for Finance App**:
- **Database Data**: PostgreSQL needs persistent storage for transaction data
- **File Uploads**: Receipt images must survive pod restarts
- **Cache Data**: Redis persistence for performance
- **Backup Data**: Snapshots and backups require persistent storage

**Storage Hierarchy in Kubernetes**:
```
┌─────────────────────────────────────────────────────────────┐
│                    Storage Layers                           │
│                                                             │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │   Application   │    │         Kubernetes              │ │
│  │     Layer       │    │         Layer                   │ │
│  │                 │    │                                 │ │
│  │ • Database      │◄──►│ • PVC (Request)                 │ │
│  │ • File Storage  │    │ • PV (Actual Volume)            │ │
│  │ • Cache         │    │ • Storage Class (Template)      │ │
│  └─────────────────┘    └─────────────────────────────────┘ │
│                                         │                   │
│                                         ▼                   │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                 AWS Layer                               │ │
│  │                                                         │ │
│  │ • EBS Volumes (Persistent)                              │ │
│  │ • Instance Store (Ephemeral)                            │ │
│  │ • EFS (Shared)                                          │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 🗃️ **Step 1: Create Namespace**

**Why use namespaces**:
- **Organization**: Separate different applications
- **Security**: Apply different policies per namespace
- **Resource Quotas**: Limit resource usage per namespace
- **Multi-tenancy**: Multiple teams can use same cluster

```bash
# Create namespace for our finance application
kubectl create namespace $NAMESPACE

# Verify namespace creation
kubectl get namespaces
# Should show finance-app namespace

# Set default namespace for convenience
kubectl config set-context --current --namespace=$NAMESPACE

# Verify current namespace
kubectl config view --minify | grep namespace
```

### 💾 **Step 2: Create Persistent Volume Claims**

**PVC Design Decisions for Finance App**:

| Component | Size | Access Mode | Storage Class | Reason |
|-----------|------|-------------|---------------|---------|
| PostgreSQL | 20Gi | ReadWriteOnce | ebs-gp3 | Database growth, single writer |
| Uploads | 10Gi | ReadWriteOnce | ebs-gp3 | Receipt files, single writer |
| Redis | 5Gi | ReadWriteOnce | ebs-gp3 | Cache persistence, single writer |

#### **PostgreSQL PVC**

```bash
cat <<EOF > postgres-pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: $NAMESPACE
  labels:
    app: postgres
    component: database
    tier: data
spec:
  accessModes:
    - ReadWriteOnce  # Only one pod can write (database requirement)
  storageClassName: ebs-gp3
  resources:
    requests:
      storage: 20Gi  # Sufficient for transaction data and growth
EOF

# Apply PostgreSQL PVC
kubectl apply -f postgres-pvc.yaml
```

**Why 20Gi for PostgreSQL**:
- Transaction data grows over time
- Indexes require additional space
- WAL (Write-Ahead Logging) files
- Room for database maintenance operations

#### **Application Uploads PVC**

```bash
cat <<EOF > uploads-pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: uploads-pvc
  namespace: $NAMESPACE
  labels:
    app: finance-app
    component: storage
    tier: files
spec:
  accessModes:
    - ReadWriteOnce  # File uploads from single app instance
  storageClassName: ebs-gp3
  resources:
    requests:
      storage: 10Gi  # Receipt images and documents
EOF

# Apply uploads PVC
kubectl apply -f uploads-pvc.yaml
```

**Why 10Gi for uploads**:
- Receipt images (typically 1-5MB each)
- Document attachments
- Thumbnail generation
- Archive storage

#### **Redis PVC**

```bash
cat <<EOF > redis-pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: redis-pvc
  namespace: $NAMESPACE
  labels:
    app: redis
    component: cache
    tier: memory
spec:
  accessModes:
    - ReadWriteOnce  # Redis single instance
  storageClassName: ebs-gp3
  resources:
    requests:
      storage: 5Gi  # AOF and RDB files
EOF

# Apply Redis PVC
kubectl apply -f redis-pvc.yaml
```

**Why 5Gi for Redis**:
- AOF (Append Only File) for persistence
- RDB snapshots for backups
- Memory dump files
- Log files

### ✅ **Step 3: Verify PVC Creation**

```bash
# Check all PVCs
kubectl get pvc -n $NAMESPACE

# Expected output (PVCs will be Pending until pods are created):
# NAME           STATUS    VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS   AGE
# postgres-pvc   Pending                                      ebs-gp3        1m
# uploads-pvc    Pending                                      ebs-gp3        1m
# redis-pvc      Pending                                      ebs-gp3        1m

# Get detailed PVC information
kubectl describe pvc postgres-pvc -n $NAMESPACE
kubectl describe pvc uploads-pvc -n $NAMESPACE
kubectl describe pvc redis-pvc -n $NAMESPACE
```

**Why PVCs are Pending**:
- **WaitForFirstConsumer**: Volumes created when pods are scheduled
- **Efficiency**: Volume created in same AZ as pod
- **Cost Optimization**: No unused volumes

### 🔧 **Step 4: Create ConfigMap for Application Configuration**

**What goes in ConfigMap vs Secrets**:
- **ConfigMap**: Non-sensitive configuration (database URLs, app settings)
- **Secrets**: Sensitive data (passwords, API keys, certificates)

```bash
cat <<EOF > configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: finance-app-config
  namespace: $NAMESPACE
  labels:
    app: finance-app
    component: config
data:
  # Database configuration
  DATABASE_URL: "postgresql://financeuser:financepass@postgres-service:5432/financedb"
  
  # Redis configuration
  REDIS_URL: "redis://:redispass123@redis-service:6379/0"
  CACHE_TYPE: "redis"
  CACHE_REDIS_URL: "redis://:redispass123@redis-service:6379/1"
  
  # Application configuration
  FLASK_ENV: "production"
  UPLOAD_FOLDER: "/app/static/uploads/receipts"
  MAX_CONTENT_LENGTH: "16777216"  # 16MB file upload limit
  
  # Logging configuration
  LOG_LEVEL: "INFO"
  LOG_FORMAT: "json"
EOF

# Apply ConfigMap
kubectl apply -f configmap.yaml
```

**ConfigMap Explanation**:
- **DATABASE_URL**: Complete PostgreSQL connection string
- **REDIS_URL**: Redis connection for caching
- **FLASK_ENV**: Production mode for Flask
- **UPLOAD_FOLDER**: Where receipt files are stored
- **MAX_CONTENT_LENGTH**: File upload size limit

### 🔐 **Step 5: Create Secrets for Sensitive Data**

```bash
cat <<EOF > secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: finance-app-secrets
  namespace: $NAMESPACE
  labels:
    app: finance-app
    component: security
type: Opaque
data:
  # Application secrets (base64 encoded)
  SECRET_KEY: $(echo -n 'your-super-secret-key-change-this-in-production' | base64)
  
  # Database credentials
  POSTGRES_PASSWORD: $(echo -n 'financepass' | base64)
  POSTGRES_USER: $(echo -n 'financeuser' | base64)
  POSTGRES_DB: $(echo -n 'financedb' | base64)
  
  # Redis credentials
  REDIS_PASSWORD: $(echo -n 'redispass123' | base64)
EOF

# Apply Secrets
kubectl apply -f secrets.yaml
```

**Security Best Practices for Secrets**:
- Use strong, randomly generated passwords
- Rotate secrets regularly
- Use external secret management (AWS Secrets Manager) in production
- Never commit secrets to version control

### 👤 **Step 6: Create Service Account**

```bash
# Apply the service account we created earlier
kubectl apply -f finance-app-service-account.yaml

# Verify service account creation
kubectl get serviceaccounts -n $NAMESPACE
# Should show finance-app-sa
```

### 📊 **Step 7: Verify All Resources**

```bash
# Check all resources in namespace
kubectl get all,pvc,configmap,secret,serviceaccount -n $NAMESPACE

# Expected output:
# - 3 PVCs in Pending state
# - 1 ConfigMap with application config
# - 1 Secret with sensitive data
# - 1 ServiceAccount for the application

# Verify ConfigMap data
kubectl describe configmap finance-app-config -n $NAMESPACE

# Verify Secret (data will be shown as <hidden>)
kubectl describe secret finance-app-secrets -n $NAMESPACE
```

### 🔍 **Storage Troubleshooting**

**Common Storage Issues**:

1. **PVC Stuck in Pending**:
```bash
# Check storage class exists
kubectl get storageclass

# Check EBS CSI driver is running
kubectl get pods -n kube-system | grep ebs-csi

# Check events
kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp'
```

2. **Volume Mount Failures**:
```bash
# Check pod events
kubectl describe pod <pod-name> -n $NAMESPACE

# Check node capacity
kubectl describe nodes

# Check volume attachment
kubectl get volumeattachments
```

3. **Permission Issues**:
```bash
# Check EBS CSI driver permissions
kubectl logs -n kube-system -l app=ebs-csi-controller

# Verify IAM role
aws iam get-role --role-name AmazonEKS_EBS_CSI_DriverRole
```

### 💡 **Storage Best Practices**

1. **Sizing**: Start with reasonable sizes, use volume expansion when needed
2. **Backup**: Implement regular EBS snapshots
3. **Monitoring**: Monitor disk usage and IOPS
4. **Security**: Enable encryption for all volumes
5. **Cost**: Use appropriate volume types for workload
6. **Availability**: Consider multi-AZ for critical data

### 📈 **Storage Monitoring**

```bash
# Check volume usage in pods (after deployment)
kubectl exec -it <pod-name> -n $NAMESPACE -- df -h

# Check EBS volume details
aws ec2 describe-volumes --filters "Name=tag:kubernetes.io/cluster/$CLUSTER_NAME,Values=owned"

# Monitor IOPS and throughput in CloudWatch
# - VolumeReadOps/VolumeWriteOps
# - VolumeThroughputPercentage
# - VolumeQueueLength
```

---
## Application Components Deployment

### 🏗️ **Deployment Strategy Overview**

**Why Deploy in This Order**:
1. **Database First**: Application depends on database
2. **Cache Second**: Application may use cache
3. **Application Last**: Depends on both database and cache

**Deployment Dependencies**:
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │      Redis      │    │  Finance App    │
│   (Database)    │◄───┤     (Cache)     │◄───┤  (Application)  │
│                 │    │                 │    │                 │
│ • Data Storage  │    │ • Session Store │    │ • Business      │
│ • ACID          │    │ • Query Cache   │    │   Logic         │
│ • Persistence   │    │ • Rate Limiting │    │ • User Interface│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 🐘 **Step 1: Deploy PostgreSQL Database**

**Why PostgreSQL for Finance App**:
- **ACID Compliance**: Ensures data consistency for financial transactions
- **Mature**: Battle-tested in production environments
- **Features**: JSON support, full-text search, advanced indexing
- **Backup**: Point-in-time recovery capabilities

#### **PostgreSQL StatefulSet Configuration**

```bash
cat <<EOF > postgres-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: $NAMESPACE
  labels:
    app: postgres
    component: database
    tier: data
spec:
  serviceName: postgres-service  # Headless service for stable network identity
  replicas: 1  # Single instance for simplicity (can be scaled later)
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
        component: database
        tier: data
    spec:
      containers:
      - name: postgres
        image: postgres:13  # Stable, well-supported version
        ports:
        - containerPort: 5432
          name: postgres
        
        # Environment variables for PostgreSQL configuration
        env:
        - name: POSTGRES_DB
          valueFrom:
            secretKeyRef:
              name: finance-app-secrets
              key: POSTGRES_DB
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: finance-app-secrets
              key: POSTGRES_USER
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: finance-app-secrets
              key: POSTGRES_PASSWORD
        - name: PGDATA
          value: /var/lib/postgresql/data/pgdata  # Custom data directory
        
        # Volume mount for persistent data
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        
        # Resource limits to prevent resource exhaustion
        resources:
          requests:
            memory: "256Mi"  # Minimum memory required
            cpu: "250m"      # 0.25 CPU cores
          limits:
            memory: "512Mi"  # Maximum memory allowed
            cpu: "500m"      # 0.5 CPU cores
        
        # Health checks
        livenessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - \$(POSTGRES_USER)
            - -d
            - \$(POSTGRES_DB)
          initialDelaySeconds: 30  # Wait 30s before first check
          periodSeconds: 10        # Check every 10s
          timeoutSeconds: 5        # Timeout after 5s
          failureThreshold: 3      # Restart after 3 failures
        
        readinessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - \$(POSTGRES_USER)
            - -d
            - \$(POSTGRES_DB)
          initialDelaySeconds: 5   # Check readiness quickly
          periodSeconds: 5         # Check every 5s
          timeoutSeconds: 3        # Quick timeout for readiness
          failureThreshold: 3      # Mark unready after 3 failures
  
  # Volume claim template for StatefulSet
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: ebs-gp3
      resources:
        requests:
          storage: 20Gi

---
# PostgreSQL Service for internal communication
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: $NAMESPACE
  labels:
    app: postgres
    component: database
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
    protocol: TCP
    name: postgres
  type: ClusterIP  # Internal access only
EOF

# Deploy PostgreSQL
kubectl apply -f postgres-statefulset.yaml
```

**StatefulSet vs Deployment for PostgreSQL**:
- **StatefulSet**: Provides stable network identity (postgres-0)
- **Ordered Deployment**: Ensures single instance starts properly
- **Persistent Storage**: Each replica gets its own volume
- **Graceful Scaling**: Controlled scaling for databases

**Health Checks Explained**:
- **Liveness Probe**: Uses `pg_isready` to check if PostgreSQL is alive
- **Readiness Probe**: Ensures PostgreSQL is ready to accept connections
- **Failure Handling**: Kubernetes restarts unhealthy containers

### 🔴 **Step 2: Deploy Redis Cache**

**Why Redis for Finance App**:
- **Performance**: In-memory storage for fast access
- **Session Storage**: Store user sessions
- **Query Caching**: Cache expensive database queries
- **Rate Limiting**: Implement API rate limiting

```bash
cat <<EOF > redis-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: $NAMESPACE
  labels:
    app: redis
    component: cache
    tier: memory
spec:
  replicas: 1  # Single instance for simplicity
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
        component: cache
        tier: memory
    spec:
      containers:
      - name: redis
        image: redis:7-alpine  # Latest stable Redis with Alpine for smaller size
        ports:
        - containerPort: 6379
          name: redis
        
        # Redis configuration via command line
        command:
          - redis-server
          - --requirepass          # Enable password authentication
          - \$(REDIS_PASSWORD)
          - --appendonly           # Enable AOF persistence
          - yes
          - --appendfsync          # Sync frequency for durability
          - everysec
          - --maxmemory            # Set memory limit
          - 256mb
          - --maxmemory-policy     # Eviction policy when memory limit reached
          - allkeys-lru            # Remove least recently used keys
        
        env:
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: finance-app-secrets
              key: REDIS_PASSWORD
        
        # Volume mount for Redis data persistence
        volumeMounts:
        - name: redis-data
          mountPath: /data
        
        # Resource limits
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        
        # Health checks
        livenessProbe:
          exec:
            command:
            - redis-cli
            - --no-auth-warning
            - -a
            - \$(REDIS_PASSWORD)
            - ping
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        
        readinessProbe:
          exec:
            command:
            - redis-cli
            - --no-auth-warning
            - -a
            - \$(REDIS_PASSWORD)
            - ping
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
      
      volumes:
      - name: redis-data
        persistentVolumeClaim:
          claimName: redis-pvc

---
# Redis Service for internal communication
apiVersion: v1
kind: Service
metadata:
  name: redis-service
  namespace: $NAMESPACE
  labels:
    app: redis
    component: cache
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
    protocol: TCP
    name: redis
  type: ClusterIP
  sessionAffinity: ClientIP  # Ensure requests go to same Redis instance
EOF

# Deploy Redis
kubectl apply -f redis-deployment.yaml
```

**Redis Configuration Explained**:
- **--requirepass**: Password authentication for security
- **--appendonly yes**: AOF persistence for data durability
- **--maxmemory 256mb**: Prevent Redis from using too much memory
- **--maxmemory-policy allkeys-lru**: Remove least recently used keys when full

### 🌐 **Step 3: Deploy Finance Application**

**Application Architecture**:
- **Flask Framework**: Python web framework
- **Gunicorn**: WSGI server for production
- **Init Container**: Waits for database to be ready
- **Health Checks**: Ensures application is healthy

```bash
cat <<EOF > finance-app-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: finance-app
  namespace: $NAMESPACE
  labels:
    app: finance-app
    component: web
    tier: application
spec:
  replicas: 2  # Run 2 instances for high availability
  selector:
    matchLabels:
      app: finance-app
  
  # Rolling update strategy for zero-downtime deployments
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # Allow 1 extra pod during updates
      maxUnavailable: 0  # Keep all pods running during updates
  
  template:
    metadata:
      labels:
        app: finance-app
        component: web
        tier: application
    spec:
      serviceAccountName: finance-app-sa  # Use our service account
      
      # Init container to wait for database
      initContainers:
      - name: wait-for-postgres
        image: postgres:13
        command: ['sh', '-c']
        args:
        - |
          until pg_isready -h postgres-service -p 5432 -U financeuser; do
            echo "Waiting for PostgreSQL..."
            sleep 2
          done
          echo "PostgreSQL is ready!"
        env:
        - name: PGPASSWORD
          valueFrom:
            secretKeyRef:
              name: finance-app-secrets
              key: POSTGRES_PASSWORD
      
      containers:
      - name: finance-app
        image: prameshwar884/personal-finance-tracker-web:latest  # Your Docker image
        ports:
        - containerPort: 5000
          name: http
        
        # Environment variables
        env:
        # Database configuration
        - name: DATABASE_URL
          valueFrom:
            configMapKeyRef:
              name: finance-app-config
              key: DATABASE_URL
        
        # Redis configuration
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: finance-app-config
              key: REDIS_URL
        - name: CACHE_TYPE
          valueFrom:
            configMapKeyRef:
              name: finance-app-config
              key: CACHE_TYPE
        - name: CACHE_REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: finance-app-config
              key: CACHE_REDIS_URL
        
        # Application secrets
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: finance-app-secrets
              key: SECRET_KEY
        
        # File upload configuration
        - name: UPLOAD_FOLDER
          valueFrom:
            configMapKeyRef:
              name: finance-app-config
              key: UPLOAD_FOLDER
        - name: MAX_CONTENT_LENGTH
          valueFrom:
            configMapKeyRef:
              name: finance-app-config
              key: MAX_CONTENT_LENGTH
        - name: FLASK_ENV
          valueFrom:
            configMapKeyRef:
              name: finance-app-config
              key: FLASK_ENV
        
        # Volume mounts
        volumeMounts:
        - name: uploads-volume
          mountPath: /app/static/uploads
        
        # Resource limits
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        
        # Health checks
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 60  # Wait for app to start
          periodSeconds: 30        # Check every 30s
          timeoutSeconds: 5        # Timeout after 5s
          failureThreshold: 3      # Restart after 3 failures
        
        readinessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30  # Check readiness after 30s
          periodSeconds: 10        # Check every 10s
          timeoutSeconds: 3        # Quick timeout for readiness
          failureThreshold: 3      # Mark unready after 3 failures
      
      volumes:
      - name: uploads-volume
        persistentVolumeClaim:
          claimName: uploads-pvc
EOF

# Deploy Finance Application
kubectl apply -f finance-app-deployment.yaml
```

**Deployment Strategy Explained**:
- **replicas: 2**: High availability with load distribution
- **RollingUpdate**: Zero-downtime deployments
- **maxSurge: 1**: Allow one extra pod during updates
- **maxUnavailable: 0**: Keep service running during updates

**Init Container Purpose**:
- Ensures database is ready before app starts
- Prevents application startup failures
- Uses `pg_isready` to check PostgreSQL availability

### ✅ **Step 4: Deploy All Components**

```bash
# Deploy in correct order
echo "🚀 Deploying PostgreSQL..."
kubectl apply -f postgres-statefulset.yaml

echo "⏳ Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n $NAMESPACE --timeout=300s

echo "🚀 Deploying Redis..."
kubectl apply -f redis-deployment.yaml

echo "⏳ Waiting for Redis to be ready..."
kubectl wait --for=condition=ready pod -l app=redis -n $NAMESPACE --timeout=300s

echo "🚀 Deploying Finance Application..."
kubectl apply -f finance-app-deployment.yaml

echo "⏳ Waiting for Finance App to be ready..."
kubectl wait --for=condition=ready pod -l app=finance-app -n $NAMESPACE --timeout=300s

echo "✅ All components deployed successfully!"
```

### 🔍 **Step 5: Verify Deployment**

```bash
# Check all pods
kubectl get pods -n $NAMESPACE

# Expected output:
# NAME                           READY   STATUS    RESTARTS   AGE
# finance-app-xxxxxxxxx-xxxxx    1/1     Running   0          2m
# finance-app-xxxxxxxxx-xxxxx    1/1     Running   0          2m
# postgres-0                     1/1     Running   0          5m
# redis-xxxxxxxxx-xxxxx          1/1     Running   0          3m

# Check all resources
kubectl get all -n $NAMESPACE

# Check PVC status (should all be Bound now)
kubectl get pvc -n $NAMESPACE

# Check services
kubectl get services -n $NAMESPACE
```

### 🧪 **Step 6: Test Application Connectivity**

```bash
# Test database connectivity from app pod
kubectl exec -it deployment/finance-app -n $NAMESPACE -- python -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    print('✅ Database connection successful!')
    cursor = conn.cursor()
    cursor.execute('SELECT version();')
    version = cursor.fetchone()
    print(f'PostgreSQL version: {version[0]}')
    conn.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
"

# Test application health endpoint
kubectl exec -it deployment/finance-app -n $NAMESPACE -- curl -s http://localhost:5000/health

# Test Redis connectivity (if Redis client is available in your image)
kubectl exec -it deployment/redis -n $NAMESPACE -- redis-cli -a \$REDIS_PASSWORD ping
```

### 📊 **Step 7: Monitor Deployment**

```bash
# Watch pod status in real-time
kubectl get pods -n $NAMESPACE -w

# Check pod logs
kubectl logs -f deployment/finance-app -n $NAMESPACE
kubectl logs -f deployment/redis -n $NAMESPACE
kubectl logs -f statefulset/postgres -n $NAMESPACE

# Check events for troubleshooting
kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp'

# Check resource usage
kubectl top pods -n $NAMESPACE
```

### 🚨 **Common Deployment Issues and Solutions**

1. **Pod Stuck in Pending**:
```bash
# Check node resources
kubectl describe nodes

# Check PVC status
kubectl get pvc -n $NAMESPACE

# Check events
kubectl describe pod <pod-name> -n $NAMESPACE
```

2. **Init Container Failing**:
```bash
# Check init container logs
kubectl logs <pod-name> -c wait-for-postgres -n $NAMESPACE

# Verify database service
kubectl get service postgres-service -n $NAMESPACE
```

3. **Application Not Ready**:
```bash
# Check application logs
kubectl logs deployment/finance-app -n $NAMESPACE

# Test health endpoint manually
kubectl exec -it deployment/finance-app -n $NAMESPACE -- curl http://localhost:5000/health
```

4. **Database Connection Issues**:
```bash
# Verify database is running
kubectl exec -it postgres-0 -n $NAMESPACE -- pg_isready

# Check database logs
kubectl logs postgres-0 -n $NAMESPACE

# Verify secrets
kubectl get secret finance-app-secrets -n $NAMESPACE -o yaml
```

---
## NGINX Ingress Controller Setup

### 🌐 **Understanding Ingress and Why You Need It**

**What is Kubernetes Ingress?**
- **HTTP/HTTPS Router**: Routes external traffic to internal services
- **Layer 7 Load Balancer**: Works at application layer (not just TCP/UDP)
- **Single Entry Point**: One load balancer for multiple services
- **SSL Termination**: Handles HTTPS certificates centrally
- **Path-based Routing**: Route different URLs to different services

**Why Use Ingress Instead of LoadBalancer Services?**

| Aspect | LoadBalancer Service | Ingress Controller |
|--------|---------------------|-------------------|
| **Cost** | $18/month per service | $18/month total |
| **SSL/TLS** | Manual certificate management | Automatic with cert-manager |
| **Routing** | Basic port-based | Advanced path/host-based |
| **Features** | Limited | Rate limiting, auth, redirects |
| **Scalability** | One LB per service | One LB for all services |

**How Ingress Benefits Your Finance App**:
```
┌─────────────────────────────────────────────────────────────┐
│                    Internet Traffic                         │
│                         │                                   │
│                         ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              AWS Load Balancer                          │ │
│  │                 (Single $18/month)                      │ │
│  └─────────────────────┬───────────────────────────────────┘ │
│                        │                                     │
│                        ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │            NGINX Ingress Controller                     │ │
│  │                                                         │ │
│  │  Routes based on:                                       │ │
│  │  • finance-app.com/        → Finance App               │ │
│  │  • finance-app.com/api/    → API Service               │ │
│  │  • finance-app.com/admin/  → Admin Panel               │ │
│  └─────────────────────┬───────────────────────────────────┘ │
│                        │                                     │
│           ┌────────────┼────────────┐                        │
│           ▼            ▼            ▼                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │Finance App  │ │ API Service │ │Admin Panel  │            │
│  │ Service     │ │   Service   │ │  Service    │            │
│  └─────────────┘ └─────────────┘ └─────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

### 🔧 **Step 1: Install NGINX Ingress Controller**

**Why NGINX Ingress Controller?**
- **Production Ready**: Battle-tested in thousands of deployments
- **Feature Rich**: Rate limiting, authentication, SSL, redirects
- **Performance**: High throughput and low latency
- **Community**: Large community and extensive documentation
- **AWS Integration**: Works well with AWS Load Balancer Controller

#### **Method 1: Using Helm (Recommended)**

```bash
# Add NGINX Ingress Helm repository
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

# Install NGINX Ingress Controller
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.service.type=LoadBalancer \
  --set controller.service.annotations."service\.beta\.kubernetes\.io/aws-load-balancer-type"="nlb" \
  --set controller.service.annotations."service\.beta\.kubernetes\.io/aws-load-balancer-scheme"="internet-facing" \
  --set controller.service.annotations."service\.beta\.kubernetes\.io/aws-load-balancer-cross-zone-load-balancing-enabled"="true" \
  --set controller.metrics.enabled=true \
  --set controller.podAnnotations."prometheus\.io/scrape"="true" \
  --set controller.podAnnotations."prometheus\.io/port"="10254"

# Wait for deployment to complete
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s
```

**Helm Installation Parameters Explained**:
- **--namespace ingress-nginx**: Dedicated namespace for ingress controller
- **--create-namespace**: Create namespace if it doesn't exist
- **service.type=LoadBalancer**: Create AWS Network Load Balancer
- **aws-load-balancer-type=nlb**: Use Network Load Balancer (better performance)
- **internet-facing**: Make load balancer accessible from internet
- **cross-zone-load-balancing**: Distribute traffic across AZs
- **metrics.enabled**: Enable Prometheus metrics for monitoring

#### **Method 2: Using kubectl (Alternative)**

```bash
# Apply NGINX Ingress Controller manifests
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/aws/deploy.yaml

# Wait for deployment
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s
```

### ✅ **Step 2: Verify NGINX Ingress Controller Installation**

```bash
# Check ingress controller pods
kubectl get pods -n ingress-nginx

# Expected output:
# NAME                                        READY   STATUS    RESTARTS   AGE
# ingress-nginx-controller-xxxxxxxxxx-xxxxx   1/1     Running   0          2m

# Check ingress controller service
kubectl get service -n ingress-nginx

# Expected output:
# NAME                                 TYPE           CLUSTER-IP      EXTERNAL-IP                                                               PORT(S)                      AGE
# ingress-nginx-controller             LoadBalancer   10.100.xxx.xxx  axxxxxxxxxxxxxxxxxxxxx-xxxxxxxxxx.elb.us-east-1.amazonaws.com          80:32000/TCP,443:31000/TCP   2m
# ingress-nginx-controller-admission   ClusterIP      10.100.xxx.xxx  <none>                                                                    443/TCP                      2m

# Get the external IP/hostname of the load balancer
INGRESS_HOST=$(kubectl get service ingress-nginx-controller -n ingress-nginx -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo "Ingress Controller External Host: $INGRESS_HOST"

# Test ingress controller health
curl -I http://$INGRESS_HOST/healthz
# Should return: HTTP/1.1 200 OK
```

### 🏗️ **Step 3: Create Application Service for Ingress**

**Why We Need a Service for Ingress**:
- Ingress routes to Services, not directly to Pods
- Services provide stable endpoints for Ingress
- Load balancing across multiple Pod replicas

```bash
cat <<EOF > finance-app-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: finance-app-service
  namespace: $NAMESPACE
  labels:
    app: finance-app
    component: web
    tier: application
  annotations:
    # Annotations for monitoring and documentation
    prometheus.io/scrape: "true"
    prometheus.io/port: "80"
    prometheus.io/path: "/metrics"
    service.alpha.kubernetes.io/description: "Finance Tracker Web Application Service"
spec:
  type: ClusterIP  # Internal service for ingress
  selector:
    app: finance-app
  ports:
  - port: 80          # Service port (what ingress connects to)
    targetPort: 5000  # Container port (where Flask app listens)
    protocol: TCP
    name: http
  # Session affinity ensures user sessions stick to same pod
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 3600  # 1 hour session stickiness
EOF

# Apply the service
kubectl apply -f finance-app-service.yaml

# Verify service creation
kubectl get service finance-app-service -n $NAMESPACE
```

### 📝 **Step 4: Create Ingress Resource**

**Understanding Ingress Resource**:
- **Rules**: Define how to route traffic
- **Paths**: URL paths to match
- **Backends**: Services to route traffic to
- **TLS**: SSL/HTTPS configuration

```bash
cat <<EOF > finance-app-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: finance-app-ingress
  namespace: $NAMESPACE
  labels:
    app: finance-app
    component: ingress
  annotations:
    # Specify ingress controller to use
    kubernetes.io/ingress.class: "nginx"
    
    # NGINX-specific annotations
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "false"  # Allow HTTP for now
    
    # Security headers
    nginx.ingress.kubernetes.io/configuration-snippet: |
      add_header X-Frame-Options "SAMEORIGIN" always;
      add_header X-Content-Type-Options "nosniff" always;
      add_header X-XSS-Protection "1; mode=block" always;
      add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Rate limiting (optional)
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
    
    # Client body size for file uploads
    nginx.ingress.kubernetes.io/proxy-body-size: "16m"
    
    # Timeouts
    nginx.ingress.kubernetes.io/proxy-connect-timeout: "60"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "60"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "60"

spec:
  rules:
  # Rule 1: Default host (using load balancer hostname)
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: finance-app-service
            port:
              number: 80
  
  # Rule 2: Custom domain (when you have one)
  # - host: finance-tracker.yourdomain.com
  #   http:
  #     paths:
  #     - path: /
  #       pathType: Prefix
  #       backend:
  #         service:
  #           name: finance-app-service
  #           port:
  #             number: 80
  
  # TLS configuration (uncomment when you have SSL certificates)
  # tls:
  # - hosts:
  #   - finance-tracker.yourdomain.com
  #   secretName: finance-app-tls
EOF

# Apply the ingress resource
kubectl apply -f finance-app-ingress.yaml

# Verify ingress creation
kubectl get ingress finance-app-ingress -n $NAMESPACE
```

**Ingress Annotations Explained**:

- **kubernetes.io/ingress.class**: Specifies which ingress controller to use
- **nginx.ingress.kubernetes.io/rewrite-target**: Rewrites URL path before forwarding
- **nginx.ingress.kubernetes.io/ssl-redirect**: Controls HTTP to HTTPS redirection
- **nginx.ingress.kubernetes.io/rate-limit**: Limits requests per client IP
- **nginx.ingress.kubernetes.io/proxy-body-size**: Max request body size (for file uploads)
- **configuration-snippet**: Custom NGINX configuration for security headers

### 🔍 **Step 5: Verify Ingress Configuration**

```bash
# Check ingress status
kubectl get ingress finance-app-ingress -n $NAMESPACE

# Expected output:
# NAME                   CLASS   HOSTS   ADDRESS                                                                   PORTS   AGE
# finance-app-ingress    nginx   *       axxxxxxxxxxxxxxxxxxxxx-xxxxxxxxxx.elb.us-east-1.amazonaws.com          80      2m

# Get detailed ingress information
kubectl describe ingress finance-app-ingress -n $NAMESPACE

# Check ingress controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller

# Verify backend service is healthy
kubectl get endpoints finance-app-service -n $NAMESPACE
```

### 🌍 **Step 6: Access Your Application**

#### **Method 1: Using Load Balancer Hostname**

```bash
# Get the load balancer hostname
INGRESS_HOST=$(kubectl get service ingress-nginx-controller -n ingress-nginx -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo "Access your application at: http://$INGRESS_HOST"

# Test the application
curl -I http://$INGRESS_HOST
# Should return: HTTP/1.1 200 OK

# Test health endpoint
curl http://$INGRESS_HOST/health
# Should return: {"status":"healthy","timestamp":"...","version":"1.0.0"}

# Open in browser (if you have a GUI)
echo "Open this URL in your browser: http://$INGRESS_HOST"
```

#### **Method 2: Using Custom Domain (Production)**

If you have a custom domain:

```bash
# 1. Create DNS record pointing to load balancer
# Create a CNAME record:
# finance-tracker.yourdomain.com → axxxxxxxxxxxxxxxxxxxxx-xxxxxxxxxx.elb.us-east-1.amazonaws.com

# 2. Update ingress to use custom domain
kubectl patch ingress finance-app-ingress -n $NAMESPACE --type='json' -p='[
  {
    "op": "add",
    "path": "/spec/rules/0/host",
    "value": "finance-tracker.yourdomain.com"
  }
]'

# 3. Access via custom domain
curl -H "Host: finance-tracker.yourdomain.com" http://$INGRESS_HOST
```

### 🧪 **Step 7: Testing Without DNS (Local Testing Trick)**

**Method 1: Using /etc/hosts File**

```bash
# Get the load balancer IP (may take a few minutes to resolve)
INGRESS_IP=$(nslookup $INGRESS_HOST | grep 'Address:' | tail -1 | awk '{print $2}')
echo "Load Balancer IP: $INGRESS_IP"

# Add entry to /etc/hosts (requires sudo)
echo "$INGRESS_IP finance-tracker.local" | sudo tee -a /etc/hosts

# Test with custom hostname
curl http://finance-tracker.local/health

# Access in browser: http://finance-tracker.local

# Clean up when done
sudo sed -i '/finance-tracker.local/d' /etc/hosts
```

**Method 2: Using Host Header**

```bash
# Test with Host header (simulates DNS)
curl -H "Host: finance-tracker.yourdomain.com" http://$INGRESS_HOST/health

# Test different paths
curl -H "Host: finance-tracker.yourdomain.com" http://$INGRESS_HOST/
curl -H "Host: finance-tracker.yourdomain.com" http://$INGRESS_HOST/login
curl -H "Host: finance-tracker.yourdomain.com" http://$INGRESS_HOST/dashboard
```

**Method 3: Port Forwarding (Development)**

```bash
# Port forward ingress controller for local testing
kubectl port-forward -n ingress-nginx service/ingress-nginx-controller 8080:80

# Access via localhost
curl http://localhost:8080/health
echo "Access your application at: http://localhost:8080"

# Stop port forwarding with Ctrl+C
```

### 🔒 **Step 8: Enable HTTPS with SSL/TLS (Optional)**

#### **Install cert-manager for Automatic SSL**

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.2/cert-manager.yaml

# Wait for cert-manager to be ready
kubectl wait --for=condition=ready pod -l app=cert-manager -n cert-manager --timeout=120s

# Create Let's Encrypt ClusterIssuer
cat <<EOF > letsencrypt-issuer.yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com  # Replace with your email
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF

kubectl apply -f letsencrypt-issuer.yaml
```

#### **Update Ingress for HTTPS**

```bash
# Update ingress with TLS configuration
cat <<EOF > finance-app-ingress-https.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: finance-app-ingress
  namespace: $NAMESPACE
  annotations:
    kubernetes.io/ingress.class: "nginx"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"  # Force HTTPS
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/configuration-snippet: |
      add_header X-Frame-Options "SAMEORIGIN" always;
      add_header X-Content-Type-Options "nosniff" always;
      add_header X-XSS-Protection "1; mode=block" always;
      add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
spec:
  tls:
  - hosts:
    - finance-tracker.yourdomain.com
    secretName: finance-app-tls
  rules:
  - host: finance-tracker.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: finance-app-service
            port:
              number: 80
EOF

# Apply updated ingress
kubectl apply -f finance-app-ingress-https.yaml

# Check certificate status
kubectl get certificate -n $NAMESPACE
kubectl describe certificate finance-app-tls -n $NAMESPACE
```

### 📊 **Step 9: Monitor Ingress Performance**

```bash
# Check ingress controller metrics
kubectl get --raw /metrics | grep nginx

# View ingress controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller -f

# Check ingress resource events
kubectl get events -n $NAMESPACE | grep ingress

# Monitor backend service health
kubectl get endpoints finance-app-service -n $NAMESPACE

# Test application performance
time curl -s http://$INGRESS_HOST/health
```

### 🔧 **Advanced Ingress Features**

#### **Path-based Routing**

```bash
cat <<EOF > advanced-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: finance-app-advanced-ingress
  namespace: $NAMESPACE
  annotations:
    kubernetes.io/ingress.class: "nginx"
    nginx.ingress.kubernetes.io/rewrite-target: /\$2
spec:
  rules:
  - http:
      paths:
      # Main application
      - path: /
        pathType: Prefix
        backend:
          service:
            name: finance-app-service
            port:
              number: 80
      # API endpoints
      - path: /api(/|$)(.*)
        pathType: Prefix
        backend:
          service:
            name: finance-app-service
            port:
              number: 80
      # Static files (if you have a separate service)
      # - path: /static
      #   pathType: Prefix
      #   backend:
      #     service:
      #       name: static-files-service
      #       port:
      #         number: 80
EOF
```

#### **Authentication with Basic Auth**

```bash
# Create basic auth secret
htpasswd -c auth admin
kubectl create secret generic basic-auth --from-file=auth -n $NAMESPACE

# Update ingress with auth
kubectl patch ingress finance-app-ingress -n $NAMESPACE --type='json' -p='[
  {
    "op": "add",
    "path": "/metadata/annotations/nginx.ingress.kubernetes.io~1auth-type",
    "value": "basic"
  },
  {
    "op": "add",
    "path": "/metadata/annotations/nginx.ingress.kubernetes.io~1auth-secret",
    "value": "basic-auth"
  },
  {
    "op": "add",
    "path": "/metadata/annotations/nginx.ingress.kubernetes.io~1auth-realm",
    "value": "Authentication Required - Finance Tracker"
  }
]'
```

### 🚨 **Troubleshooting Ingress Issues**

#### **Common Issues and Solutions**

1. **502 Bad Gateway**:
```bash
# Check backend service
kubectl get endpoints finance-app-service -n $NAMESPACE

# Check pod health
kubectl get pods -n $NAMESPACE
kubectl logs deployment/finance-app -n $NAMESPACE

# Check service selector
kubectl describe service finance-app-service -n $NAMESPACE
```

2. **404 Not Found**:
```bash
# Check ingress rules
kubectl describe ingress finance-app-ingress -n $NAMESPACE

# Check ingress controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller --tail=50
```

3. **SSL Certificate Issues**:
```bash
# Check certificate status
kubectl get certificate -n $NAMESPACE
kubectl describe certificate finance-app-tls -n $NAMESPACE

# Check cert-manager logs
kubectl logs -n cert-manager -l app=cert-manager
```

4. **Load Balancer Not Ready**:
```bash
# Check AWS Load Balancer Controller
kubectl logs -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller

# Check security groups
aws ec2 describe-security-groups --filters "Name=tag:kubernetes.io/cluster/$CLUSTER_NAME,Values=owned"
```

### 💡 **Ingress Best Practices**

1. **Security**:
   - Always use HTTPS in production
   - Implement rate limiting
   - Add security headers
   - Use authentication when needed

2. **Performance**:
   - Enable gzip compression
   - Set appropriate timeouts
   - Use connection pooling
   - Monitor response times

3. **Reliability**:
   - Configure health checks
   - Set up monitoring and alerting
   - Use multiple ingress controllers for HA
   - Implement circuit breakers

4. **Cost Optimization**:
   - Use single ingress for multiple services
   - Implement proper caching
   - Monitor bandwidth usage
   - Use appropriate instance types

### 📈 **Benefits Summary for Your Finance App**

1. **Cost Savings**: One load balancer instead of multiple ($18/month vs $54/month)
2. **SSL Management**: Automatic certificate provisioning and renewal
3. **Advanced Routing**: Path-based routing for API vs web traffic
4. **Security**: Built-in security headers and rate limiting
5. **Scalability**: Easy to add new services behind same ingress
6. **Monitoring**: Built-in metrics and logging
7. **Professional URLs**: Clean URLs instead of random load balancer hostnames

Your finance application is now accessible via a professional ingress setup with advanced routing, security, and monitoring capabilities!

---
## Monitoring with Prometheus and Grafana

### 📊 **Understanding Monitoring Stack**

**Why Monitor Your Finance Application?**
- **Performance**: Track response times, throughput, and resource usage
- **Reliability**: Detect issues before users notice them
- **Capacity Planning**: Understand when to scale resources
- **Business Metrics**: Monitor user activity, transaction volumes
- **Troubleshooting**: Quickly identify root causes of problems
- **Compliance**: Meet regulatory requirements for financial applications

**Monitoring Stack Architecture**:
```
┌─────────────────────────────────────────────────────────────────┐
│                    Monitoring Architecture                      │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐ │
│  │    Grafana      │    │   Prometheus    │    │ Application │ │
│  │  (Visualization)│◄───┤   (Metrics)     │◄───┤   Metrics   │ │
│  │                 │    │                 │    │             │ │
│  │ • Dashboards    │    │ • Time Series   │    │ • /metrics  │ │
│  │ • Alerts        │    │ • Queries       │    │ • Health    │ │
│  │ • Reports       │    │ • Storage       │    │ • Custom    │ │
│  └─────────────────┘    └─────────────────┘    └─────────────┘ │
│           │                        │                    │       │
│           └────────────────────────┼────────────────────┘       │
│                                    │                            │
│  ┌─────────────────────────────────┼──────────────────────────┐ │
│  │              Targets            │                          │ │
│  │                                 ▼                          │ │
│  │ • Kubernetes API     • Node Exporter                      │ │
│  │ • Finance App        • PostgreSQL Exporter                │ │
│  │ • Redis Exporter     • NGINX Ingress                      │ │
│  │ • EBS CSI Driver     • AWS Load Balancer                  │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

**Components Explained**:
- **Prometheus**: Collects and stores metrics as time series data
- **Grafana**: Creates beautiful dashboards and visualizations
- **Exporters**: Convert application metrics to Prometheus format
- **AlertManager**: Handles alerts and notifications
- **ServiceMonitor**: Kubernetes custom resource for service discovery

### 🔧 **Step 1: Install Prometheus Stack using Helm**

**Why use kube-prometheus-stack?**
- **Complete Solution**: Prometheus, Grafana, AlertManager in one package
- **Pre-configured**: Ready-to-use dashboards and alerts
- **Kubernetes Native**: Designed specifically for Kubernetes monitoring
- **Community Maintained**: Regular updates and security patches

```bash
# Add Prometheus community Helm repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Create monitoring namespace
kubectl create namespace monitoring

# Install kube-prometheus-stack
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
  --set prometheus.prometheusSpec.podMonitorSelectorNilUsesHelmValues=false \
  --set prometheus.prometheusSpec.retention=30d \
  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.storageClassName=ebs-gp3 \
  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=20Gi \
  --set grafana.adminPassword=admin123 \
  --set grafana.persistence.enabled=true \
  --set grafana.persistence.storageClassName=ebs-gp3 \
  --set grafana.persistence.size=10Gi \
  --set alertmanager.alertmanagerSpec.storage.volumeClaimTemplate.spec.storageClassName=ebs-gp3 \
  --set alertmanager.alertmanagerSpec.storage.volumeClaimTemplate.spec.resources.requests.storage=5Gi

# Wait for all components to be ready
echo "⏳ Waiting for Prometheus stack to be ready..."
kubectl wait --for=condition=ready pod -l "app.kubernetes.io/name=prometheus" -n monitoring --timeout=300s
kubectl wait --for=condition=ready pod -l "app.kubernetes.io/name=grafana" -n monitoring --timeout=300s
```

**Installation Parameters Explained**:
- **serviceMonitorSelectorNilUsesHelmValues=false**: Discover all ServiceMonitors
- **retention=30d**: Keep metrics for 30 days
- **storageClassName=ebs-gp3**: Use our EBS storage class
- **grafana.adminPassword**: Set Grafana admin password
- **persistence.enabled=true**: Enable persistent storage for dashboards

### ✅ **Step 2: Verify Prometheus Stack Installation**

```bash
# Check all monitoring pods
kubectl get pods -n monitoring

# Expected output:
# NAME                                                     READY   STATUS    RESTARTS   AGE
# alertmanager-prometheus-kube-prometheus-alertmanager-0   2/2     Running   0          3m
# prometheus-grafana-xxxxxxxxxx-xxxxx                     3/3     Running   0          3m
# prometheus-kube-prometheus-operator-xxxxxxxxxx-xxxxx    1/1     Running   0          3m
# prometheus-kube-state-metrics-xxxxxxxxxx-xxxxx          1/1     Running   0          3m
# prometheus-prometheus-kube-prometheus-prometheus-0       2/2     Running   0          3m
# prometheus-prometheus-node-exporter-xxxxx               1/1     Running   0          3m
# prometheus-prometheus-node-exporter-xxxxx               1/1     Running   0          3m

# Check services
kubectl get services -n monitoring

# Check persistent volumes
kubectl get pvc -n monitoring

# Verify Prometheus is scraping targets
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090 &
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets | length'
# Should return number of active targets being monitored
```

### 🌐 **Step 3: Create NodePort Services for External Access**

**Why NodePort for Testing?**
- **Quick Access**: No need to set up ingress or load balancers
- **Development**: Easy testing during development
- **Troubleshooting**: Direct access for debugging
- **Cost Effective**: No additional load balancer costs

#### **Prometheus NodePort Service**

```bash
cat <<EOF > prometheus-nodeport.yaml
apiVersion: v1
kind: Service
metadata:
  name: prometheus-nodeport
  namespace: monitoring
  labels:
    app: prometheus
    component: server
spec:
  type: NodePort
  selector:
    app.kubernetes.io/name: prometheus
    prometheus: prometheus-kube-prometheus-prometheus
  ports:
  - port: 9090
    targetPort: 9090
    nodePort: 30090  # External port on nodes
    protocol: TCP
    name: web
EOF

# Apply Prometheus NodePort service
kubectl apply -f prometheus-nodeport.yaml
```

#### **Grafana NodePort Service**

```bash
cat <<EOF > grafana-nodeport.yaml
apiVersion: v1
kind: Service
metadata:
  name: grafana-nodeport
  namespace: monitoring
  labels:
    app: grafana
    component: grafana
spec:
  type: NodePort
  selector:
    app.kubernetes.io/name: grafana
  ports:
  - port: 3000
    targetPort: 3000
    nodePort: 30300  # External port on nodes
    protocol: TCP
    name: web
EOF

# Apply Grafana NodePort service
kubectl apply -f grafana-nodeport.yaml
```

#### **AlertManager NodePort Service (Optional)**

```bash
cat <<EOF > alertmanager-nodeport.yaml
apiVersion: v1
kind: Service
metadata:
  name: alertmanager-nodeport
  namespace: monitoring
  labels:
    app: alertmanager
    component: alertmanager
spec:
  type: NodePort
  selector:
    app.kubernetes.io/name: alertmanager
    alertmanager: prometheus-kube-prometheus-alertmanager
  ports:
  - port: 9093
    targetPort: 9093
    nodePort: 30093  # External port on nodes
    protocol: TCP
    name: web
EOF

# Apply AlertManager NodePort service
kubectl apply -f alertmanager-nodeport.yaml
```

### 🔍 **Step 4: Test Access via NodePort**

```bash
# Get node external IPs
kubectl get nodes -o wide

# Expected output:
# NAME                            STATUS   ROLES    AGE   VERSION               INTERNAL-IP     EXTERNAL-IP      OS-IMAGE         KERNEL-VERSION                  CONTAINER-RUNTIME
# ip-192-168-0-152.ec2.internal   Ready    <none>   2h    v1.28.x-eks-xxxxx     192.168.0.152   3.238.238.92     Amazon Linux 2   5.10.239-236.958.amzn2.x86_64   containerd://1.7.27
# ip-192-168-43-36.ec2.internal   Ready    <none>   2h    v1.28.x-eks-xxxxx     192.168.43.36   34.200.218.171   Amazon Linux 2   5.10.239-236.958.amzn2.x86_64   containerd://1.7.27

# Store node IPs for easy access
NODE1_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="ExternalIP")].address}')
NODE2_IP=$(kubectl get nodes -o jsonpath='{.items[1].status.addresses[?(@.type=="ExternalIP")].address}')

echo "Node 1 IP: $NODE1_IP"
echo "Node 2 IP: $NODE2_IP"

# Test Prometheus access
echo "🔍 Testing Prometheus access..."
curl -I http://$NODE1_IP:30090
# Should return: HTTP/1.1 200 OK

echo "📊 Prometheus Web UI: http://$NODE1_IP:30090"
echo "📊 Alternative:       http://$NODE2_IP:30090"

# Test Grafana access
echo "🎨 Testing Grafana access..."
curl -I http://$NODE1_IP:30300
# Should return: HTTP/1.1 200 OK

echo "📈 Grafana Web UI: http://$NODE1_IP:30300"
echo "📈 Alternative:    http://$NODE2_IP:30300"
echo "📈 Login: admin / admin123"

# Test AlertManager access
echo "🚨 Testing AlertManager access..."
curl -I http://$NODE1_IP:30093
# Should return: HTTP/1.1 200 OK

echo "🚨 AlertManager Web UI: http://$NODE1_IP:30093"
echo "🚨 Alternative:          http://$NODE2_IP:30093"
```

**Note**: If external access doesn't work, you may need to update AWS security groups:

```bash
# Get the security group for your worker nodes
SECURITY_GROUP=$(aws ec2 describe-instances \
  --filters "Name=tag:kubernetes.io/cluster/$CLUSTER_NAME,Values=owned" \
  --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' \
  --output text)

echo "Worker node security group: $SECURITY_GROUP"

# Add rules for NodePort access (30090, 30300, 30093)
aws ec2 authorize-security-group-ingress \
  --group-id $SECURITY_GROUP \
  --protocol tcp \
  --port 30090 \
  --cidr 0.0.0.0/0 \
  --tag-specifications 'ResourceType=security-group-rule,Tags=[{Key=Name,Value=prometheus-nodeport}]'

aws ec2 authorize-security-group-ingress \
  --group-id $SECURITY_GROUP \
  --protocol tcp \
  --port 30300 \
  --cidr 0.0.0.0/0 \
  --tag-specifications 'ResourceType=security-group-rule,Tags=[{Key=Name,Value=grafana-nodeport}]'

aws ec2 authorize-security-group-ingress \
  --group-id $SECURITY_GROUP \
  --protocol tcp \
  --port 30093 \
  --cidr 0.0.0.0/0 \
  --tag-specifications 'ResourceType=security-group-rule,Tags=[{Key=Name,Value=alertmanager-nodeport}]'

echo "✅ Security group rules added for NodePort access"
```

### 📊 **Step 5: Configure Application Monitoring**

#### **Add Metrics to Your Finance Application**

First, update your Flask application to expose metrics:

```python
# Add to your Flask application (requirements.txt)
# prometheus-flask-exporter==0.21.0

# Add to your Flask app code
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
metrics = PrometheusMetrics(app)

# Custom metrics for finance app
from prometheus_client import Counter, Histogram, Gauge

# Business metrics
transaction_counter = Counter('finance_transactions_total', 'Total transactions', ['type'])
user_login_counter = Counter('finance_user_logins_total', 'Total user logins')
receipt_upload_counter = Counter('finance_receipts_uploaded_total', 'Total receipts uploaded')

# Performance metrics
request_duration = Histogram('finance_request_duration_seconds', 'Request duration')
active_users = Gauge('finance_active_users', 'Currently active users')

# Example usage in your routes
@app.route('/api/transaction', methods=['POST'])
def create_transaction():
    transaction_counter.labels(type='income').inc()  # or 'expense'
    # ... your transaction logic
    return jsonify({'status': 'success'})

@app.route('/login', methods=['POST'])
def login():
    user_login_counter.inc()
    # ... your login logic
    return jsonify({'status': 'success'})
```

#### **Create ServiceMonitor for Your Application**

```bash
cat <<EOF > finance-app-servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: finance-app-monitor
  namespace: $NAMESPACE
  labels:
    app: finance-app
    release: prometheus  # Important: matches Prometheus selector
spec:
  selector:
    matchLabels:
      app: finance-app
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
  namespaceSelector:
    matchNames:
    - $NAMESPACE
EOF

# Apply ServiceMonitor
kubectl apply -f finance-app-servicemonitor.yaml

# Verify ServiceMonitor is created
kubectl get servicemonitor -n $NAMESPACE
```

#### **Update Finance App Service with Metrics Annotations**

```bash
# Update your finance app service to include metrics annotations
kubectl patch service finance-app-service -n $NAMESPACE --type='json' -p='[
  {
    "op": "add",
    "path": "/metadata/annotations/prometheus.io~1scrape",
    "value": "true"
  },
  {
    "op": "add",
    "path": "/metadata/annotations/prometheus.io~1port",
    "value": "80"
  },
  {
    "op": "add",
    "path": "/metadata/annotations/prometheus.io~1path",
    "value": "/metrics"
  }
]'

# Verify annotations
kubectl describe service finance-app-service -n $NAMESPACE
```

### 🎨 **Step 6: Access and Configure Grafana**

#### **Initial Grafana Setup**

1. **Access Grafana Web UI**:
   ```bash
   echo "📈 Grafana URL: http://$NODE1_IP:30300"
   echo "📈 Username: admin"
   echo "📈 Password: admin123"
   ```

2. **Login to Grafana**:
   - Open the URL in your browser
   - Login with admin/admin123
   - You may be prompted to change the password

3. **Verify Prometheus Data Source**:
   - Go to Configuration → Data Sources
   - Should see "Prometheus" already configured
   - URL should be: `http://prometheus-kube-prometheus-prometheus:9090`

#### **Import Pre-built Dashboards**

```bash
# Get some popular dashboard IDs for Kubernetes monitoring:
# - Kubernetes Cluster Monitoring: 7249
# - Node Exporter Full: 1860
# - Kubernetes Pod Monitoring: 6417
# - NGINX Ingress Controller: 9614

echo "📊 Popular Grafana Dashboard IDs to import:"
echo "   • Kubernetes Cluster: 7249"
echo "   • Node Exporter: 1860"
echo "   • Pod Monitoring: 6417"
echo "   • NGINX Ingress: 9614"
echo ""
echo "To import:"
echo "1. Go to Grafana → + → Import"
echo "2. Enter dashboard ID"
echo "3. Select Prometheus data source"
echo "4. Click Import"
```

#### **Create Custom Dashboard for Finance App**

```bash
cat <<EOF > finance-app-dashboard.json
{
  "dashboard": {
    "id": null,
    "title": "Personal Finance Tracker",
    "tags": ["finance", "application"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Application Health",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"finance-app-service\"}",
            "legendFormat": "App Status"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "thresholds"
            },
            "thresholds": {
              "steps": [
                {"color": "red", "value": 0},
                {"color": "green", "value": 1}
              ]
            }
          }
        },
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(flask_http_request_total[5m])",
            "legendFormat": "Requests/sec"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
      },
      {
        "id": 3,
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "flask_http_request_duration_seconds",
            "legendFormat": "Response Time"
          }
        ],
        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8}
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "30s"
  }
}
EOF

echo "📊 Custom dashboard JSON created: finance-app-dashboard.json"
echo "To import: Grafana → + → Import → Upload JSON file"
```

### 🔍 **Step 7: Verify Monitoring is Working**

#### **Check Prometheus Targets**

1. **Access Prometheus UI**: `http://$NODE1_IP:30090`
2. **Go to Status → Targets**
3. **Verify targets are UP**:
   - kubernetes-apiservers
   - kubernetes-nodes
   - kubernetes-pods
   - kubernetes-service-endpoints
   - Your finance-app (if ServiceMonitor is working)

#### **Test Prometheus Queries**

```bash
# Port forward Prometheus for API testing
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090 &

# Test some basic queries
echo "🔍 Testing Prometheus queries..."

# Check if finance app is up
curl -s "http://localhost:9090/api/v1/query?query=up{job=\"finance-app-service\"}" | jq '.data.result[0].value[1]'

# Check node CPU usage
curl -s "http://localhost:9090/api/v1/query?query=100-(avg(rate(node_cpu_seconds_total{mode=\"idle\"}[5m]))*100)" | jq '.data.result[0].value[1]'

# Check memory usage
curl -s "http://localhost:9090/api/v1/query?query=100*((node_memory_MemTotal_bytes-node_memory_MemAvailable_bytes)/node_memory_MemTotal_bytes)" | jq '.data.result[0].value[1]'

# Stop port forwarding
pkill -f "kubectl port-forward.*prometheus"
```

#### **Generate Test Traffic**

```bash
# Generate some traffic to your finance app for monitoring
INGRESS_HOST=$(kubectl get service ingress-nginx-controller -n ingress-nginx -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Generate test requests
for i in {1..100}; do
  curl -s http://$INGRESS_HOST/health > /dev/null
  echo "Request $i sent"
  sleep 1
done

echo "✅ Test traffic generated. Check Grafana dashboards for metrics!"
```

### 📈 **Step 8: Set Up Basic Alerts**

#### **Create AlertManager Configuration**

```bash
cat <<EOF > alertmanager-config.yaml
apiVersion: v1
kind: Secret
metadata:
  name: alertmanager-prometheus-kube-prometheus-alertmanager
  namespace: monitoring
type: Opaque
stringData:
  alertmanager.yml: |
    global:
      smtp_smarthost: 'localhost:587'
      smtp_from: 'alerts@finance-tracker.com'
    
    route:
      group_by: ['alertname']
      group_wait: 10s
      group_interval: 10s
      repeat_interval: 1h
      receiver: 'web.hook'
    
    receivers:
    - name: 'web.hook'
      webhook_configs:
      - url: 'http://127.0.0.1:5001/'
        send_resolved: true
    
    # Email notifications (configure SMTP settings)
    # - name: 'email-notifications'
    #   email_configs:
    #   - to: 'admin@finance-tracker.com'
    #     subject: 'Finance Tracker Alert: {{ .GroupLabels.alertname }}'
    #     body: |
    #       {{ range .Alerts }}
    #       Alert: {{ .Annotations.summary }}
    #       Description: {{ .Annotations.description }}
    #       {{ end }}
EOF

# Apply AlertManager configuration
kubectl apply -f alertmanager-config.yaml

# Restart AlertManager to pick up new config
kubectl rollout restart statefulset/alertmanager-prometheus-kube-prometheus-alertmanager -n monitoring
```

#### **Create Custom Alert Rules**

```bash
cat <<EOF > finance-app-alerts.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: finance-app-alerts
  namespace: monitoring
  labels:
    prometheus: kube-prometheus
    role: alert-rules
spec:
  groups:
  - name: finance-app.rules
    rules:
    - alert: FinanceAppDown
      expr: up{job="finance-app-service"} == 0
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "Finance application is down"
        description: "Finance application has been down for more than 1 minute"
    
    - alert: HighResponseTime
      expr: flask_http_request_duration_seconds > 2
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High response time detected"
        description: "Finance app response time is above 2 seconds"
    
    - alert: HighErrorRate
      expr: rate(flask_http_request_exceptions_total[5m]) > 0.1
      for: 2m
      labels:
        severity: warning
      annotations:
        summary: "High error rate detected"
        description: "Finance app error rate is above 10%"
    
    - alert: DatabaseConnectionFailed
      expr: up{job="postgres-exporter"} == 0
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "Database connection failed"
        description: "Cannot connect to PostgreSQL database"
EOF

# Apply alert rules
kubectl apply -f finance-app-alerts.yaml

# Verify alert rules are loaded
kubectl get prometheusrules -n monitoring
```

### 🧹 **Step 9: Clean Up NodePort Services (Optional)**

When you're done testing, you can remove the NodePort services:

```bash
# Remove NodePort services
kubectl delete service prometheus-nodeport -n monitoring
kubectl delete service grafana-nodeport -n monitoring
kubectl delete service alertmanager-nodeport -n monitoring

# Remove security group rules
aws ec2 revoke-security-group-ingress \
  --group-id $SECURITY_GROUP \
  --protocol tcp \
  --port 30090 \
  --cidr 0.0.0.0/0

aws ec2 revoke-security-group-ingress \
  --group-id $SECURITY_GROUP \
  --protocol tcp \
  --port 30300 \
  --cidr 0.0.0.0/0

aws ec2 revoke-security-group-ingress \
  --group-id $SECURITY_GROUP \
  --protocol tcp \
  --port 30093 \
  --cidr 0.0.0.0/0

echo "✅ NodePort services and security group rules removed"
```

### 📊 **Monitoring Best Practices**

#### **Key Metrics to Monitor for Finance App**

1. **Application Metrics**:
   - Request rate and response time
   - Error rate and success rate
   - User login/logout events
   - Transaction processing time
   - File upload success/failure

2. **Infrastructure Metrics**:
   - CPU and memory usage
   - Disk I/O and space usage
   - Network traffic
   - Pod restart count

3. **Business Metrics**:
   - Daily active users
   - Transaction volume
   - Revenue metrics
   - Feature usage statistics

4. **Security Metrics**:
   - Failed login attempts
   - Suspicious activity patterns
   - API rate limiting triggers
   - Certificate expiration

#### **Dashboard Organization**

1. **Executive Dashboard**: High-level business metrics
2. **Operations Dashboard**: Infrastructure health and performance
3. **Application Dashboard**: Application-specific metrics
4. **Security Dashboard**: Security-related metrics and alerts

#### **Alert Strategy**

1. **Critical Alerts**: Immediate action required (app down, database failure)
2. **Warning Alerts**: Investigation needed (high response time, error rate)
3. **Info Alerts**: Awareness only (deployment events, scaling events)

### 🎯 **Summary**

You now have a complete monitoring stack for your Personal Finance Tracker:

✅ **Prometheus**: Collecting metrics from all components
✅ **Grafana**: Beautiful dashboards and visualizations  
✅ **AlertManager**: Intelligent alerting and notifications
✅ **NodePort Access**: Easy testing and development access
✅ **Custom Metrics**: Application-specific monitoring
✅ **Security**: Proper RBAC and network policies
✅ **Persistence**: Data survives pod restarts
✅ **Scalability**: Ready for production workloads

**Access URLs**:
- **Prometheus**: `http://NODE_IP:30090`
- **Grafana**: `http://NODE_IP:30300` (admin/admin123)
- **AlertManager**: `http://NODE_IP:30093`

Your finance application is now fully monitored with industry-standard tools, giving you complete visibility into performance, reliability, and business metrics!

---
