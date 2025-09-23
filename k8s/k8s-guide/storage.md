# EKS Dynamic Storage Provisioning - Complete Master Guide

## Table of Contents
1. [Complete Step-by-Step Setup](#complete-step-by-step-setup)
2. [Understanding Core Concepts](#understanding-core-concepts)
3. [OIDC Provider Management](#oidc-provider-management)
4. [Trust Policy vs Permission Policy](#trust-policy-vs-permission-policy)
5. [EBS CSI Driver Architecture](#ebs-csi-driver-architecture)
6. [Project-Specific Implementation](#project-specific-implementation)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

---

# Complete Step-by-Step Setup

## Prerequisites Check
Before starting, verify you have:
```bash
# Check AWS CLI is configured
aws sts get-caller-identity

# Check kubectl is configured for your EKS cluster
kubectl get nodes

# Check your cluster exists
aws eks list-clusters
```

---

## Step 1: Create OIDC Provider

### What is OIDC Provider?
**OIDC (OpenID Connect) Provider** is a bridge that allows Kubernetes service accounts to assume AWS IAM roles. It enables secure authentication between your EKS cluster and AWS services without storing AWS credentials in your cluster.

### Why Do We Need It?
- **Security**: No need to store AWS access keys in pods
- **Automation**: Service accounts can automatically get temporary AWS credentials
- **Least Privilege**: Each service account can have specific permissions

### Step 1.1: Get Your Cluster's OIDC Information
```bash
# Replace 'my-cluster' with your actual cluster name
CLUSTER_NAME="my-cluster"
REGION="us-east-1"

# Get OIDC issuer URL
OIDC_ISSUER=$(aws eks describe-cluster --name $CLUSTER_NAME --region $REGION --query "cluster.identity.oidc.issuer" --output text)
echo "OIDC Issuer: $OIDC_ISSUER"

# Extract OIDC ID (the last part of the URL)
OIDC_ID=$(echo $OIDC_ISSUER | cut -d '/' -f 5)
echo "OIDC ID: $OIDC_ID"

### **Step 2: Delete the unused OIDC provider**

bash
# Delete the old OIDC provider
aws iam delete-open-id-connect-provider \
    --open-id-connect-provider-arn arn:aws:iam::142595748980:oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/A369568D1731D2FD89B4B591846AFA4D

```

### Step 1.2: Check if OIDC Provider Already Exists
```bash
# List existing OIDC providers
aws iam list-open-id-connect-providers

# Check if your specific OIDC provider exists
aws iam get-open-id-connect-provider \
    --open-id-connect-provider-arn "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):oidc-provider/oidc.eks.$REGION.amazonaws.com/id/$OIDC_ID" 2>/dev/null || echo "OIDC

Provider does not exist"

```
### Step 1.3: Attached OIDC Provider to your cluster if already exist

eksctl utils associate-iam-oidc-provider \
  --cluster my-cluster \
  --region us-east-1 \
  --approve

### Step 1.4: Create OIDC Provider (if it doesn't exist)
```bash
# Create OIDC provider
aws iam create-open-id-connect-provider \
    --url $OIDC_ISSUER \
    --thumbprint-list 9e99a48a9960b14926bb7f3b02e22da2b0ab7280 \
    --client-id-list sts.amazonaws.com

echo "✅ OIDC Provider created successfully"
```

**Explanation of Parameters:**
- `--url`: Your cluster's OIDC issuer URL
- `--thumbprint-list`: Root CA thumbprint for EKS OIDC (this is a standard value)
- `--client-id-list`: Specifies that AWS STS can use this provider

---

## Step 2: Understand Trust Policy

### What is a Trust Policy?
A **Trust Policy** defines WHO can assume an IAM role. It's like a bouncer at a club - it decides who gets in.

### Why Do We Need Trust Policy?
- **Security**: Controls which entities can use the role
- **Authentication**: Verifies the identity of the requester
- **Authorization**: Grants permission to assume the role

### Trust Policy Components Explained:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",                    // ← Allow or Deny
      "Principal": {                        // ← WHO can assume this role
        "Federated": "arn:aws:iam::ACCOUNT:oidc-provider/..."
      },
      "Action": "sts:AssumeRoleWithWebIdentity",  // ← HOW they assume the role
      "Condition": {                        // ← WHEN they can assume it
        "StringEquals": {
          "oidc.eks.REGION.amazonaws.com/id/OIDC-ID:aud": "sts.amazonaws.com",
          "oidc.eks.REGION.amazonaws.com/id/OIDC-ID:sub": "system:serviceaccount:kube-system:ebs-csi-controller-sa"
        }
      }
    }
  ]
}
```

### Step 2.1: Create Trust Policy File
```bash
# Get your account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Create trust policy file
cat > ebs-csi-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::$ACCOUNT_ID:oidc-provider/oidc.eks.$REGION.amazonaws.com/id/$OIDC_ID"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "oidc.eks.$REGION.amazonaws.com/id/$OIDC_ID:aud": "sts.amazonaws.com",
          "oidc.eks.$REGION.amazonaws.com/id/$OIDC_ID:sub": "system:serviceaccount:kube-system:ebs-csi-controller-sa"
        }
      }
    }
  ]
}
EOF

echo "✅ Trust policy created: ebs-csi-trust-policy.json"
```

**Trust Policy Breakdown:**
- **Principal.Federated**: Points to your OIDC provider
- **Action**: Allows assuming role via web identity (OIDC)
- **Condition.aud**: Audience must be AWS STS
- **Condition.sub**: Subject must be the specific service account

---

## Step 3: Create IAM Role

### What is an IAM Role?
An **IAM Role** is like a job title with specific permissions. The EBS CSI driver "wears" this role to get permissions to manage EBS volumes.

### Why Do We Need This Role?
- **Permissions**: Grants access to EBS operations (create, attach, delete volumes)
- **Security**: Temporary credentials instead of permanent access keys
- **Isolation**: Only the EBS CSI driver can use this role

### Step 3.1: Create the IAM Role (with Trust Policy)
```bash
# Create IAM role with trust policy
aws iam create-role \
    --role-name AmazonEKS_EBS_CSI_DriverRole \
    --assume-role-policy-document file://ebs-csi-trust-policy.json

echo "✅ IAM Role created: AmazonEKS_EBS_CSI_DriverRole"
```

**Note**: This step attaches the **Trust Policy** (WHO can assume the role)

### Step 3.2: Attach Required Permissions (Permission Policy)
```bash
# Attach AWS managed policy for EBS CSI driver
aws iam attach-role-policy \
    --role-name AmazonEKS_EBS_CSI_DriverRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy

echo "✅ EBS CSI Driver policy attached to role"
```

**Note**: This step attaches the **Permission Policy** (WHAT the role can do)

### What Permissions Does This Policy Grant?
The `AmazonEBSCSIDriverPolicy` includes:
- **ec2:CreateVolume** - Create new EBS volumes
- **ec2:DeleteVolume** - Delete EBS volumes
- **ec2:AttachVolume** - Attach volumes to EC2 instances
- **ec2:DetachVolume** - Detach volumes from instances
- **ec2:DescribeVolumes** - Query volume information
- **ec2:CreateTags** - Tag volumes for identification
- **ec2:DescribeInstances** - Find target EC2 instances

---

## Step 4: Install EBS CSI Driver

### What is EBS CSI Driver?
The **EBS CSI (Container Storage Interface) Driver** is a Kubernetes component that:
- Translates Kubernetes storage requests into AWS EBS operations
- Manages the lifecycle of EBS volumes
- Handles mounting/unmounting volumes to pods

### Why Do We Need It?
- **Dynamic Provisioning**: Automatically creates EBS volumes when PVCs are created
- **Volume Management**: Handles attachment, formatting, and mounting
- **Kubernetes Integration**: Provides native Kubernetes storage experience

### Step 4.1: Install as EKS Add-on (Recommended)
```bash
# Install EBS CSI driver as managed add-on
aws eks create-addon \
    --cluster-name $CLUSTER_NAME \
    --addon-name aws-ebs-csi-driver \
    --service-account-role-arn "arn:aws:iam::$ACCOUNT_ID:role/AmazonEKS_EBS_CSI_DriverRole" \
    --resolve-conflicts OVERWRITE \
    --region $REGION

echo "✅ EBS CSI Driver add-on installation started"
```

### Step 4.2: Wait for Installation to Complete
```bash
# Check add-on status
while true; do
    STATUS=$(aws eks describe-addon --cluster-name $CLUSTER_NAME --addon-name aws-ebs-csi-driver --region $REGION --query "addon.status" --output text)
    if [ "$STATUS" = "ACTIVE" ]; then
        echo "✅ EBS CSI Driver is active and ready"
        break
    elif [ "$STATUS" = "CREATE_FAILED" ] || [ "$STATUS" = "DEGRADED" ]; then
        echo "❌ EBS CSI Driver installation failed"
        exit 1
    else
        echo "⏳ Add-on status: $STATUS (waiting...)"
        sleep 10
    fi
done
```

### Step 4.3: Verify Installation
```bash
# Check if CSI driver pods are running
kubectl get pods -n kube-system -l app=ebs-csi-controller
kubectl get pods -n kube-system -l app=ebs-csi-node

# Verify CSI driver is registered
kubectl get csidriver ebs.csi.aws.com

# Check service account has correct annotations
kubectl describe sa ebs-csi-controller-sa -n kube-system
```

---

## Step 5: Understand Service Accounts

### What is a Kubernetes Service Account?
A **Service Account** is like an identity card for pods. It tells Kubernetes "this pod is allowed to do certain things."

### Where is the Service Account Used?
The EBS CSI driver uses the service account `ebs-csi-controller-sa` in the `kube-system` namespace.

### How Does It Connect to AWS?
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Service Account │    │   OIDC Provider │    │    IAM Role     │
│                 │    │                 │    │                 │
│ ebs-csi-        │───▶│ Authenticates   │───▶│ Grants AWS      │
│ controller-sa   │    │ the request     │    │ permissions     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Step 5.1: Verify Service Account Annotation
```bash
# Check if service account has the correct role annotation
kubectl get sa ebs-csi-controller-sa -n kube-system -o yaml

# The annotation should look like:
# eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT:role/AmazonEKS_EBS_CSI_DriverRole
```

---

## Step 6: Create Storage Class

### What is a Storage Class?
A **Storage Class** is like a menu at a restaurant - it defines what types of storage are available and their characteristics.

### Why Do We Need Storage Classes?
- **Standardization**: Consistent storage configurations
- **Automation**: Automatic provisioning based on requirements
- **Flexibility**: Different storage types for different needs

### Step 6.1: Create Storage Class
```bash
# Create storage class for your project
kubectl apply -f - <<EOF
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: finance-tracker-storage
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
  encrypted: "true"
  fsType: ext4
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
reclaimPolicy: Delete
EOF

echo "✅ Storage class created: finance-tracker-storage"
```

### Storage Class Parameters Explained:
- **provisioner**: `ebs.csi.aws.com` - Uses EBS CSI driver
- **type**: `gp3` - Latest generation general purpose SSD
- **iops**: `3000` - Input/Output operations per second
- **throughput**: `125` - MB/s throughput (gp3 only)
- **encrypted**: `true` - Encrypt volumes at rest
- **fsType**: `ext4` - File system type
- **volumeBindingMode**: `WaitForFirstConsumer` - Create volume when pod is scheduled
- **allowVolumeExpansion**: `true` - Allow volume size increases
- **reclaimPolicy**: `Delete` - Delete EBS volume when PV is deleted

### Step 6.2: Verify Storage Class
```bash
# List all storage classes
kubectl get storageclass

# Describe your storage class
kubectl describe storageclass finance-tracker-storage
```

---

## Step 7: Create PVCs (Persistent Volume Claims)

### What are PVCs?
**PVCs** are like reservation requests at a restaurant - they ask for storage with specific requirements.

### Step 7.1: Create Namespace
```bash
# Create namespace for your application
kubectl create namespace finance-tracker
```

### Step 7.2: Create PVCs for Your Project
```bash
# Create PostgreSQL PVC
kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: finance-tracker
  labels:
    app: postgres
    component: database
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: finance-tracker-storage
  resources:
    requests:
      storage: 20Gi
EOF

# Create Uploads PVC
kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: uploads-pvc
  namespace: finance-tracker
  labels:
    app: finance-tracker
    component: storage
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: finance-tracker-storage
  resources:
    requests:
      storage: 10Gi
EOF

echo "✅ PVCs created: postgres-pvc (20Gi) and uploads-pvc (10Gi)"
```

### Step 7.3: Verify PVCs
```bash
# Check PVC status
kubectl get pvc -n finance-tracker

# Describe PVCs for more details
kubectl describe pvc postgres-pvc -n finance-tracker
kubectl describe pvc uploads-pvc -n finance-tracker
```

---

## Step 8: Understand the Complete Flow

### What Happens When You Create a PVC?

```
1. PVC Created
   ↓
2. Storage Class Referenced
   ↓
3. EBS CSI Driver Notified
   ↓
4. Service Account Assumes IAM Role
   ↓
5. EBS Volume Created in AWS
   ↓
6. PV Automatically Created
   ↓
7. PVC Bound to PV
   ↓
8. Ready for Pod to Use
```

### Step 8.1: Monitor the Process
```bash
# Watch PVCs get bound
kubectl get pvc -n finance-tracker -w

# Check events
kubectl get events -n finance-tracker --sort-by='.lastTimestamp'

# Verify PVs were created
kubectl get pv
```

### Step 8.2: Check AWS EBS Volumes
```bash
# List EBS volumes created by your cluster
aws ec2 describe-volumes \
    --filters "Name=tag:kubernetes.io/cluster/$CLUSTER_NAME,Values=owned" \
    --region $REGION \
    --query 'Volumes[*].[VolumeId,Size,State,VolumeType,Encrypted]' \
    --output table
```

---

## Step 9: Complete Verification

### Step 9.1: Verify All Components
```bash
echo "=== OIDC Provider ==="
aws iam list-open-id-connect-providers

echo "=== IAM Role ==="
aws iam get-role --role-name AmazonEKS_EBS_CSI_DriverRole

echo "=== EBS CSI Driver ==="
kubectl get pods -n kube-system | grep ebs-csi

echo "=== Storage Class ==="
kubectl get storageclass

echo "=== PVCs ==="
kubectl get pvc -n finance-tracker

echo "=== PVs ==="
kubectl get pv

echo "=== EBS Volumes ==="
aws ec2 describe-volumes --filters "Name=tag:kubernetes.io/cluster/$CLUSTER_NAME,Values=owned" --region $REGION --query 'Volumes[*].VolumeId' --output text
```

### Step 9.2: Test with a Pod
```bash
# Create a test pod to verify storage works
kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: storage-test
  namespace: finance-tracker
spec:
  containers:
  - name: test
    image: busybox
    command: ['sleep', '3600']
    volumeMounts:
    - name: postgres-storage
      mountPath: /postgres-data
    - name: uploads-storage
      mountPath: /uploads-data
  volumes:
  - name: postgres-storage
    persistentVolumeClaim:
      claimName: postgres-pvc
  - name: uploads-storage
    persistentVolumeClaim:
      claimName: uploads-pvc
EOF

# Check if pod starts successfully
kubectl get pod storage-test -n finance-tracker

# Test writing to volumes
kubectl exec -it storage-test -n finance-tracker -- sh -c "echo 'test' > /postgres-data/test.txt && echo 'test' > /uploads-data/test.txt && ls -la /postgres-data/ /uploads-data/"
```

---
# Understanding Core Concepts

## The Big Picture: How Everything Connects

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EKS Dynamic Storage Flow                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │    PVC      │───▶│Storage Class│───▶│ EBS CSI     │───▶│ EBS Volume  │  │
│  │ (Request)   │    │ (Template)  │    │ Driver      │    │ (AWS)       │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│                                              │                              │
│                                              ▼                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │Service      │───▶│OIDC Provider│───▶│ IAM Role    │───▶│ AWS API     │  │
│  │Account      │    │(Bridge)     │    │(Permissions)│    │ Calls       │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Relationships

### 1. OIDC Provider ↔ Service Account ↔ IAM Role
```
Kubernetes Service Account
         ↓ (authenticated by)
    OIDC Provider
         ↓ (allows assumption of)
      IAM Role
         ↓ (grants permissions to)
     AWS EBS API
```

### 2. PVC ↔ Storage Class ↔ EBS CSI Driver
```
PVC (What you want)
    ↓ (references)
Storage Class (How to create it)
    ↓ (uses provisioner)
EBS CSI Driver (Creates it)
    ↓ (calls)
AWS EBS API (Makes it happen)
```

---

# OIDC Provider Management

## Understanding OIDC Provider Connection to Clusters

### How to Check Which Cluster an OIDC Provider Belongs To

#### Method 1: From OIDC Provider ARN
```bash
# List all OIDC providers
aws iam list-open-id-connect-providers

# Example output:
# {
#     "OpenIDConnectProviderList": [
#         {
#             "Arn": "arn:aws:iam::142595748980:oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/31E0BE0E48C6BF612967EBEEE5C91B31"
#         }
#     ]
# }

# Extract OIDC ID from ARN (last part after /id/)
OIDC_ID="31E0BE0E48C6BF612967EBEEE5C91B31"  # From the ARN above
```

#### Method 2: Find Cluster by OIDC ID
```bash
# List all clusters and their OIDC IDs
aws eks list-clusters --query "clusters[]" --output text | while read cluster; do
    echo "Cluster: $cluster"
    aws eks describe-cluster --name $cluster --query "cluster.identity.oidc.issuer" --output text
    echo "---"
done

# Example output:
# Cluster: my-cluster
# https://oidc.eks.us-east-1.amazonaws.com/id/31E0BE0E48C6BF612967EBEEE5C91B31
# ---
# Cluster: another-cluster
# https://oidc.eks.us-east-1.amazonaws.com/id/A369568D1731D2FD89B4B591846AFA4D
# ---
```

#### Method 3: Check Specific Cluster's OIDC
```bash
# Check if a specific cluster has OIDC enabled
CLUSTER_NAME="my-cluster"
REGION="us-east-1"

# Get cluster's OIDC issuer
OIDC_ISSUER=$(aws eks describe-cluster --name $CLUSTER_NAME --region $REGION --query "cluster.identity.oidc.issuer" --output text)
echo "Cluster: $CLUSTER_NAME"
echo "OIDC Issuer: $OIDC_ISSUER"

# Extract OIDC ID
OIDC_ID=$(echo $OIDC_ISSUER | cut -d '/' -f 5)
echo "OIDC ID: $OIDC_ID"

# Check if OIDC provider exists for this cluster
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws iam get-open-id-connect-provider \
    --open-id-connect-provider-arn "arn:aws:iam::$ACCOUNT_ID:oidc-provider/oidc.eks.$REGION.amazonaws.com/id/$OIDC_ID" \
    2>/dev/null && echo "✅ OIDC Provider exists" || echo "❌ OIDC Provider does not exist"
```

### OIDC Provider Details
```bash
# Get detailed information about an OIDC provider
OIDC_PROVIDER_ARN="arn:aws:iam::142595748980:oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/31E0BE0E48C6BF612967EBEEE5C91B31"

aws iam get-open-id-connect-provider --open-id-connect-provider-arn $OIDC_PROVIDER_ARN

# Example output shows:
# - URL: The OIDC issuer URL
# - ClientIDList: Usually ["sts.amazonaws.com"]
# - ThumbprintList: Root CA thumbprint
# - CreateDate: When it was created
```

## How to Delete OIDC Provider

### ⚠️ **WARNING: Be Very Careful!**
Deleting an OIDC provider will break all IAM roles that depend on it. This includes:
- EBS CSI Driver
- AWS Load Balancer Controller
- Cluster Autoscaler
- Any other service using IRSA (IAM Roles for Service Accounts)

### Step 1: Check What Uses the OIDC Provider
```bash
# Find all IAM roles that trust this OIDC provider
OIDC_ID="31E0BE0E48C6BF612967EBEEE5C91B31"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "Checking which IAM roles use this OIDC provider..."

# List all roles and check their trust policies
aws iam list-roles --query "Roles[*].RoleName" --output text | while read role; do
    TRUST_POLICY=$(aws iam get-role --role-name $role --query "Role.AssumeRolePolicyDocument" --output json 2>/dev/null)
    if echo $TRUST_POLICY | grep -q $OIDC_ID; then
        echo "Role using OIDC: $role"
    fi
done
```

### Step 2: Delete Dependent Resources First
```bash
# Example: Delete EBS CSI Driver add-on first
aws eks delete-addon --cluster-name my-cluster --addon-name aws-ebs-csi-driver

# Delete IAM roles that use the OIDC provider
aws iam delete-role --role-name AmazonEKS_EBS_CSI_DriverRole
```

### Step 3: Delete OIDC Provider
```bash
# Delete the OIDC provider
OIDC_PROVIDER_ARN="arn:aws:iam::142595748980:oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/31E0BE0E48C6BF612967EBEEE5C91B31"

aws iam delete-open-id-connect-provider --open-id-connect-provider-arn $OIDC_PROVIDER_ARN

echo "✅ OIDC Provider deleted"
```

### Alternative: Safe Deletion Script
```bash
#!/bin/bash
# Safe OIDC provider deletion script

CLUSTER_NAME="my-cluster"
REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Get OIDC details
OIDC_ISSUER=$(aws eks describe-cluster --name $CLUSTER_NAME --region $REGION --query "cluster.identity.oidc.issuer" --output text)
OIDC_ID=$(echo $OIDC_ISSUER | cut -d '/' -f 5)
OIDC_PROVIDER_ARN="arn:aws:iam::$ACCOUNT_ID:oidc-provider/oidc.eks.$REGION.amazonaws.com/id/$OIDC_ID"

echo "🔍 Checking dependencies for OIDC Provider: $OIDC_PROVIDER_ARN"

# Check for dependent roles
echo "Roles using this OIDC provider:"
aws iam list-roles --query "Roles[*].RoleName" --output text | while read role; do
    if aws iam get-role --role-name $role --query "Role.AssumeRolePolicyDocument" --output json 2>/dev/null | grep -q $OIDC_ID; then
        echo "  - $role"
    fi
done

echo ""
read -p "⚠️  Are you sure you want to delete this OIDC provider? This will break all dependent services! (yes/no): " confirm

if [ "$confirm" = "yes" ]; then
    echo "🗑️  Deleting OIDC provider..."
    aws iam delete-open-id-connect-provider --open-id-connect-provider-arn $OIDC_PROVIDER_ARN
    echo "✅ OIDC Provider deleted"
else
    echo "❌ Deletion cancelled"
fi
```

## OIDC Provider Best Practices

### 1. One OIDC Provider per Cluster
- Each EKS cluster should have its own OIDC provider
- Don't share OIDC providers between clusters
- OIDC ID is unique per cluster

### 2. Check Before Creating
```bash
# Always check if OIDC provider exists before creating
CLUSTER_NAME="my-cluster"
REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
OIDC_ID=$(aws eks describe-cluster --name $CLUSTER_NAME --region $REGION --query "cluster.identity.oidc.issuer" --output text | cut -d '/' -f 5)

if aws iam get-open-id-connect-provider --open-id-connect-provider-arn "arn:aws:iam::$ACCOUNT_ID:oidc-provider/oidc.eks.$REGION.amazonaws.com/id/$OIDC_ID" >/dev/null 2>&1; then
    echo "✅ OIDC Provider already exists"
else
    echo "❌ OIDC Provider does not exist - creating..."
    # Create OIDC provider
fi
```

### 3. Document Your OIDC Providers
```bash
# Create a documentation script
#!/bin/bash
echo "=== OIDC Provider Documentation ==="
echo "Account: $(aws sts get-caller-identity --query Account --output text)"
echo "Region: us-east-1"
echo ""

aws iam list-open-id-connect-providers --query "OpenIDConnectProviderList[*].Arn" --output text | while read arn; do
    echo "OIDC Provider: $arn"
    OIDC_ID=$(echo $arn | cut -d '/' -f 5)
    
    # Find which cluster this belongs to
    aws eks list-clusters --query "clusters[]" --output text | while read cluster; do
        CLUSTER_OIDC=$(aws eks describe-cluster --name $cluster --query "cluster.identity.oidc.issuer" --output text | cut -d '/' -f 5)
        if [ "$CLUSTER_OIDC" = "$OIDC_ID" ]; then
            echo "  Belongs to cluster: $cluster"
        fi
    done
    
    # Find dependent roles
    echo "  Dependent IAM roles:"
    aws iam list-roles --query "Roles[*].RoleName" --output text | while read role; do
        if aws iam get-role --role-name $role --query "Role.AssumeRolePolicyDocument" --output json 2>/dev/null | grep -q $OIDC_ID; then
            echo "    - $role"
        fi
    done
    echo ""
done
```

---
# Trust Policy vs Permission Policy

## Complete Explanation with Examples

### Visual Comparison
```
┌─────────────────────────────────────────────────────────────────┐
│                        IAM Role                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────┐    ┌─────────────────────────────────┐ │
│  │   Trust Policy      │    │      Permission Policy         │ │
│  │   (Step 3.1)        │    │      (Step 3.2)                │ │
│  │                     │    │                                 │ │
│  │ WHO can assume      │    │ WHAT the role can do           │ │
│  │ this role?          │    │                                 │ │
│  │                     │    │ • ec2:CreateVolume             │ │
│  │ • OIDC Provider     │    │ • ec2:AttachVolume             │ │
│  │ • Service Account   │    │ • ec2:DetachVolume             │ │
│  │ • Specific          │    │ • ec2:DescribeVolumes          │ │
│  │   conditions        │    │ • ec2:DeleteVolume             │ │
│  │                     │    │ • ec2:CreateTags               │ │
│  └─────────────────────┘    └─────────────────────────────────┘ │
│           │                              │                      │
│           ▼                              ▼                      │
│  "Can this entity        "What AWS APIs can                     │
│   assume this role?"      this role call?"                      │
└─────────────────────────────────────────────────────────────────┘
```

## Trust Policy (WHO) - You Create This

### Purpose
Controls **WHO** can "wear" this role

### When You Create It
**Step 3.1**: When creating the IAM role
```bash
aws iam create-role \
    --role-name AmazonEKS_EBS_CSI_DriverRole \
    --assume-role-policy-document file://ebs-csi-trust-policy.json
    #                                    ↑
    #                            This is the TRUST POLICY
```

### Content (Your Custom Trust Policy)
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::142595748980:oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/31E0BE0E48C6BF612967EBEEE5C91B31"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "oidc.eks.us-east-1.amazonaws.com/id/31E0BE0E48C6BF612967EBEEE5C91B31:aud": "sts.amazonaws.com",
          "oidc.eks.us-east-1.amazonaws.com/id/31E0BE0E48C6BF612967EBEEE5C91B31:sub": "system:serviceaccount:kube-system:ebs-csi-controller-sa"
        }
      }
    }
  ]
}
```

### Translation
"Only the `ebs-csi-controller-sa` service account from the `kube-system` namespace, authenticated through our OIDC provider, can assume this role."

## Permission Policy (WHAT) - AWS Already Created This

### Purpose
Defines **WHAT** AWS actions the role can perform

### When You Attach It
**Step 3.2**: After creating the role
```bash
aws iam attach-role-policy \
    --role-name AmazonEKS_EBS_CSI_DriverRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy
    #                                                    ↑
    #                                    This is the PERMISSION POLICY (AWS Managed)
```

### Status
✅ **Already exists** - AWS created and maintains it

### Content (AWS Managed Policy)
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeAvailabilityZones",
        "ec2:DescribeInstances",
        "ec2:DescribeSnapshots",
        "ec2:DescribeTags",
        "ec2:DescribeVolumes",
        "ec2:DescribeVolumesModifications",
        "ec2:DescribeVolumeStatus"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:CreateSnapshot",
        "ec2:ModifyVolume"
      ],
      "Resource": "arn:aws:ec2:*:*:volume/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:AttachVolume",
        "ec2:DetachVolume"
      ],
      "Resource": [
        "arn:aws:ec2:*:*:volume/*",
        "arn:aws:ec2:*:*:instance/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:CreateVolume"
      ],
      "Resource": "arn:aws:ec2:*:*:volume/*",
      "Condition": {
        "StringLike": {
          "aws:RequestTag/ebs.csi.aws.com/cluster": "true"
        }
      }
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DeleteVolume"
      ],
      "Resource": "arn:aws:ec2:*:*:volume/*",
      "Condition": {
        "StringLike": {
          "ec2:ResourceTag/ebs.csi.aws.com/cluster": "true"
        }
      }
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:CreateTags"
      ],
      "Resource": [
        "arn:aws:ec2:*:*:volume/*",
        "arn:aws:ec2:*:*:snapshot/*"
      ],
      "Condition": {
        "StringEquals": {
          "ec2:CreateAction": [
            "CreateVolume",
            "CreateSnapshot"
          ]
        }
      }
    }
  ]
}
```

### Translation
"This role can create, delete, attach, detach, and manage EBS volumes and snapshots with specific conditions for security."

## How They Work Together

### Authentication Flow
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  EBS CSI Pod    │    │   Trust Policy  │    │ Permission      │
│                 │    │                 │    │ Policy          │
│ 1. "I want to   │───▶│ 2. "Are you     │───▶│ 3. "Yes, you    │
│    assume this  │    │    allowed to   │    │    can create   │
│    role"        │    │    assume this  │    │    EBS volumes" │
│                 │    │    role?"       │    │                 │
│                 │◄───│                 │◄───│                 │
│ 6. Gets temp    │    │ 5. "Yes, here   │    │ 4. Role assumed │
│    credentials  │    │    are your     │    │    successfully │
│                 │    │    credentials" │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Real-World Analogy

### Trust Policy = Security Guard
- Checks your ID (service account)
- Verifies you're on the list (OIDC authentication)
- Decides if you can enter (assume the role)

### Permission Policy = Access Badge
- Once inside, your badge determines what you can do
- Can you access the server room? (ec2:CreateVolume)
- Can you use the elevator? (ec2:AttachVolume)
- Can you enter meeting rooms? (ec2:DescribeVolumes)

## Summary Table

| Aspect | Trust Policy | Permission Policy |
|--------|--------------|-------------------|
| **Purpose** | WHO can assume the role | WHAT the role can do |
| **Created by** | 🔨 You | ✅ AWS (already exists) |
| **When attached** | Step 3.1 (role creation) | Step 3.2 (policy attachment) |
| **Content** | Custom for your cluster | Standard EBS permissions |
| **Maintenance** | You maintain | AWS maintains |
| **File location** | `ebs-csi-trust-policy.json` | AWS managed policy ARN |

**Both are required** because:
- Without Trust Policy: Nobody can assume the role
- Without Permission Policy: The role can't do anything useful

The **Trust Policy** is the gatekeeper, and the **Permission Policy** is the toolbox! 🔐🧰

---
# EBS CSI Driver Architecture

## Detailed Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              EKS Cluster                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Control Plane                                │   │
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐  │   │
│  │  │   API Server    │    │   Scheduler     │    │  Controller     │  │   │
│  │  │                 │    │                 │    │  Manager        │  │   │
│  │  └─────────────────┘    └─────────────────┘    └─────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Worker Nodes                                 │   │
│  │                                                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │                  EBS CSI Controller                         │   │   │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │   │   │
│  │  │  │ Provisioner │  │  Attacher   │  │    Resizer          │ │   │   │
│  │  │  │             │  │             │  │                     │ │   │   │
│  │  │  │ Creates     │  │ Attaches    │  │ Expands volumes     │ │   │   │
│  │  │  │ EBS volumes │  │ volumes to  │  │                     │ │   │   │
│  │  │  │             │  │ nodes       │  │                     │ │   │   │
│  │  │  └─────────────┘  └─────────────┘  └─────────────────────┘ │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  │                                                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │                   EBS CSI Node Plugin                       │   │   │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │   │   │
│  │  │  │   Mounter   │  │ Device      │  │    Volume           │ │   │   │
│  │  │  │             │  │ Manager     │  │    Statistics       │ │   │   │
│  │  │  │ Mounts      │  │             │  │                     │ │   │   │
│  │  │  │ volumes to  │  │ Manages     │  │ Reports usage       │ │   │   │
│  │  │  │ pods        │  │ devices     │  │                     │ │   │   │
│  │  │  └─────────────┘  └─────────────┘  └─────────────────────┘ │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                AWS EBS                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Volume    │  │   Volume    │  │  Snapshot   │  │      Encryption     │ │
│  │  Creation   │  │ Attachment  │  │  Creation   │  │                     │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## CSI Driver Components Explained

### Controller Components (Run on Control Plane)
1. **Provisioner**: Creates and deletes EBS volumes
2. **Attacher**: Attaches/detaches volumes to/from nodes
3. **Resizer**: Handles volume expansion
4. **Snapshotter**: Creates volume snapshots

### Node Components (Run on Each Worker Node)
1. **Mounter**: Mounts/unmounts volumes to/from pods
2. **Device Manager**: Manages block devices
3. **Volume Statistics**: Reports volume usage metrics

## Service Account Deep Dive

### Service Account Annotation Magic

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ebs-csi-controller-sa
  namespace: kube-system
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT:role/AmazonEKS_EBS_CSI_DriverRole
```

**What This Annotation Does:**
1. Tells EKS to inject AWS credentials into pods using this service account
2. Credentials are temporary and automatically rotated
3. Credentials have permissions defined by the IAM role

### Service Account Token Flow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│      Pod        │    │  Service        │    │   AWS STS       │
│                 │    │  Account        │    │                 │
│ 1. Starts with  │───▶│ 2. Has role     │───▶│ 3. Issues       │
│    SA attached  │    │    annotation   │    │    credentials  │
│                 │    │                 │    │                 │
│ 6. Makes AWS    │◄───│ 5. Injects      │◄───│ 4. Returns      │
│    API calls    │    │    credentials  │    │    temp token   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Storage Class Deep Dive

### Storage Class as a Template

Think of Storage Class as a template or recipe:

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: finance-tracker-storage
provisioner: ebs.csi.aws.com          # ← Which driver to use
parameters:                           # ← Recipe ingredients
  type: gp3                          # ← Volume type
  iops: "3000"                       # ← Performance level
  throughput: "125"                  # ← Speed
  encrypted: "true"                  # ← Security
  fsType: ext4                       # ← File system
volumeBindingMode: WaitForFirstConsumer # ← When to create
allowVolumeExpansion: true            # ← Can grow later
reclaimPolicy: Delete                 # ← What happens when deleted
```

### Volume Binding Modes Explained

```
┌─────────────────────────────────────────────────────────────────┐
│                    Volume Binding Modes                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────┐    ┌─────────────────────────────────┐ │
│  │     Immediate       │    │    WaitForFirstConsumer         │ │
│  │                     │    │                                 │ │
│  │ PVC Created         │    │ PVC Created                     │ │
│  │      ↓              │    │      ↓                          │ │
│  │ Volume Created      │    │ PVC stays Pending               │ │
│  │ Immediately         │    │      ↓                          │ │
│  │      ↓              │    │ Pod scheduled                   │ │
│  │ PVC Bound           │    │      ↓                          │ │
│  │      ↓              │    │ Volume created in same AZ       │ │
│  │ Pod can be          │    │      ↓                          │ │
│  │ scheduled anywhere  │    │ PVC Bound                       │ │
│  │                     │    │                                 │ │
│  │ Risk: Volume and    │    │ Benefit: Volume and pod in      │ │
│  │ pod in different AZ │    │ same AZ (better performance)    │ │
│  └─────────────────────┘    └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

**Recommendation**: Use `WaitForFirstConsumer` for EBS volumes to ensure volume and pod are in the same Availability Zone.

---

# Project-Specific Implementation

## Your Finance Tracker Storage Requirements

```
┌─────────────────────────────────────────────────────────────────┐
│                  Finance Tracker Storage                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────┐    ┌─────────────────────────────────┐ │
│  │   PostgreSQL        │    │      File Uploads               │ │
│  │                     │    │                                 │ │
│  │ • Database files    │    │ • User uploaded files           │ │
│  │ • Transaction logs  │    │ • Profile pictures              │ │
│  │ • Indexes          │    │ • Document attachments          │ │
│  │                     │    │                                 │ │
│  │ Size: 20Gi         │    │ Size: 10Gi                      │ │
│  │ Type: gp3          │    │ Type: gp3                       │ │
│  │ IOPS: 3000         │    │ IOPS: 3000                      │ │
│  │ Encrypted: Yes     │    │ Encrypted: Yes                  │ │
│  └─────────────────────┘    └─────────────────────────────────┘ │
│           │                              │                      │
│           ▼                              ▼                      │
│  ┌─────────────────────┐    ┌─────────────────────────────────┐ │
│  │   postgres-pvc      │    │      uploads-pvc                │ │
│  │                     │    │                                 │ │
│  │ Mounted at:         │    │ Mounted at:                     │ │
│  │ /var/lib/postgresql │    │ /app/uploads                    │ │
│  │ /data               │    │                                 │ │
│  └─────────────────────┘    └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Complete Deployment Example

### PostgreSQL StatefulSet with Dynamic Storage
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: finance-tracker
spec:
  serviceName: postgres-service
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:13
        env:
        - name: POSTGRES_DB
          value: "finance_tracker"
        - name: POSTGRES_USER
          value: "postgres"
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        - name: PGDATA
          value: /var/lib/postgresql/data/pgdata
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - postgres
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - postgres
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc
```

### Application Deployment with File Upload Storage
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: finance-tracker-app
  namespace: finance-tracker
spec:
  replicas: 2
  selector:
    matchLabels:
      app: finance-tracker
  template:
    metadata:
      labels:
        app: finance-tracker
    spec:
      containers:
      - name: finance-tracker
        image: your-dockerhub-username/personal-finance-tracker:latest
        ports:
        - containerPort: 5000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: database-url
        - name: UPLOAD_FOLDER
          value: "/app/uploads"
        volumeMounts:
        - name: uploads-storage
          mountPath: /app/uploads
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: uploads-storage
        persistentVolumeClaim:
          claimName: uploads-pvc
```

---

# Troubleshooting

## Common Issues and Solutions

### 1. PVC Stuck in Pending State

**Symptoms:**
```bash
kubectl get pvc -n finance-tracker
# NAME           STATUS    VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS   AGE
# postgres-pvc   Pending                                      gp3-storage    5m
```

**Diagnosis:**
```bash
# Check PVC events
kubectl describe pvc postgres-pvc -n finance-tracker

# Check storage class exists
kubectl get storageclass

# Check EBS CSI driver is running
kubectl get pods -n kube-system | grep ebs-csi
```

**Common Causes & Solutions:**
1. **Storage class doesn't exist**
   ```bash
   kubectl apply -f dynamic-storage-class.yaml
   ```

2. **EBS CSI driver not installed**
   ```bash
   aws eks describe-addon --cluster-name my-cluster --addon-name aws-ebs-csi-driver
   ```

3. **IAM permissions missing**
   ```bash
   aws iam get-role --role-name AmazonEKS_EBS_CSI_DriverRole
   ```

### 2. Pod Cannot Mount Volume

**Symptoms:**
```bash
kubectl describe pod postgres-0 -n finance-tracker
# Events:
# Warning  FailedMount  pod/postgres-0  MountVolume.MountDevice failed
```

**Diagnosis:**
```bash
# Check node plugin logs
kubectl logs -n kube-system -l app=ebs-csi-node

# Check if volume is attached to correct node
aws ec2 describe-volumes --volume-ids vol-xxxxxxxxx
```

**Common Causes & Solutions:**
1. **Volume and pod in different AZ**
   - Use `WaitForFirstConsumer` binding mode
   - Check node and volume AZ match

2. **File system not formatted**
   - Check CSI node logs for formatting errors
   - Verify `fsType` parameter in storage class

### 3. EBS CSI Driver Permission Errors

**Symptoms:**
```bash
kubectl logs -n kube-system -l app=ebs-csi-controller
# Error: AccessDenied: User: arn:aws:sts::123456789012:assumed-role/...
```

**Diagnosis:**
```bash
# Check service account annotation
kubectl describe sa ebs-csi-controller-sa -n kube-system

# Verify IAM role trust policy
aws iam get-role --role-name AmazonEKS_EBS_CSI_DriverRole

# Check attached policies
aws iam list-attached-role-policies --role-name AmazonEKS_EBS_CSI_DriverRole
```

**Solutions:**
1. **Fix service account annotation**
   ```bash
   kubectl annotate sa ebs-csi-controller-sa -n kube-system \
     eks.amazonaws.com/role-arn=arn:aws:iam::ACCOUNT:role/AmazonEKS_EBS_CSI_DriverRole
   ```

2. **Update trust policy**
   ```bash
   aws iam update-assume-role-policy \
     --role-name AmazonEKS_EBS_CSI_DriverRole \
     --policy-document file://trust-policy.json
   ```

### 4. Volume Expansion Failures

**Symptoms:**
```bash
kubectl describe pvc postgres-pvc -n finance-tracker
# Conditions:
#   Type                      Status  LastProbeTime  Reason
#   FileSystemResizePending   True                   Waiting for user to restart pod
```

**Solutions:**
1. **Restart pod to complete expansion**
   ```bash
   kubectl delete pod postgres-0 -n finance-tracker
   ```

2. **Check if storage class allows expansion**
   ```bash
   kubectl get storageclass finance-tracker-storage -o yaml | grep allowVolumeExpansion
   ```

## Debugging Commands Reference

```bash
# Check all storage resources
kubectl get storageclass,pv,pvc -A

# Check EBS CSI driver status
kubectl get pods -n kube-system | grep ebs-csi
kubectl logs -n kube-system -l app=ebs-csi-controller
kubectl logs -n kube-system -l app=ebs-csi-node

# Check service account
kubectl describe sa ebs-csi-controller-sa -n kube-system

# Check IAM role
aws iam get-role --role-name AmazonEKS_EBS_CSI_DriverRole
aws iam list-attached-role-policies --role-name AmazonEKS_EBS_CSI_DriverRole

# Check EBS volumes in AWS
aws ec2 describe-volumes --filters "Name=tag:kubernetes.io/cluster/my-cluster,Values=owned"

# Check events
kubectl get events -A --sort-by='.lastTimestamp' | grep -i volume
```

---

# Best Practices

## Security Best Practices

### 1. Encryption at Rest
```yaml
# Always encrypt volumes
parameters:
  encrypted: "true"
  kmsKeyId: "arn:aws:kms:region:account:key/key-id"  # Optional: custom key
```

### 2. Least Privilege IAM
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:CreateVolume",
        "ec2:DeleteVolume",
        "ec2:AttachVolume",
        "ec2:DetachVolume",
        "ec2:DescribeVolumes",
        "ec2:DescribeInstances",
        "ec2:CreateTags"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "ec2:Region": "us-east-1"
        }
      }
    }
  ]
}
```

### 3. Network Security
```yaml
# Use private subnets for worker nodes
# Restrict security groups
# Enable VPC flow logs
```

## Performance Best Practices

### 1. Choose Right Volume Type
```yaml
# For databases (high IOPS)
parameters:
  type: io2
  iops: "10000"

# For general purpose (balanced)
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"

# For big data (high throughput)
parameters:
  type: st1
```

### 2. Right-Size Volumes
```yaml
# Start small, allow expansion
spec:
  resources:
    requests:
      storage: 20Gi  # Start with what you need

# Enable expansion
allowVolumeExpansion: true
```

### 3. Use Appropriate Access Modes
```yaml
# For single-pod access (databases)
spec:
  accessModes:
    - ReadWriteOnce

# For multi-pod read access (shared files)
spec:
  accessModes:
    - ReadOnlyMany  # Note: EBS doesn't support this
```

## Cost Optimization

### 1. Volume Lifecycle Management
```yaml
# Delete volumes when not needed
reclaimPolicy: Delete

# Or retain for important data
reclaimPolicy: Retain
```

### 2. Monitoring and Alerting
```bash
# Monitor volume usage
kubectl top pvc -A

# Set up CloudWatch alarms for:
# - Volume utilization > 80%
# - IOPS utilization > 80%
# - Unused volumes
```

### 3. Snapshot Strategy
```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: postgres-backup
spec:
  volumeSnapshotClassName: ebs-snapshot-class
  source:
    persistentVolumeClaimName: postgres-pvc
```

## Operational Best Practices

### 1. Backup Strategy
```bash
# Regular snapshots
kubectl create volumesnapshot postgres-backup-$(date +%Y%m%d) \
  --from-pvc=postgres-pvc \
  --snapshot-class=ebs-snapshot-class

# Cross-region backup
aws ec2 copy-snapshot \
  --source-region us-east-1 \
  --source-snapshot-id snap-xxxxxxxxx \
  --destination-region us-west-2
```

### 2. Monitoring
```yaml
# Add resource requests/limits
resources:
  requests:
    storage: 20Gi
  limits:
    storage: 100Gi  # Maximum allowed expansion
```

### 3. Documentation
```yaml
# Label everything
metadata:
  labels:
    app: finance-tracker
    component: database
    environment: production
    backup-policy: daily
```

---

## 🎓 **Conclusion**

This comprehensive guide covers every aspect of EKS dynamic storage provisioning. You now understand:

- **OIDC Provider**: Bridge between Kubernetes and AWS IAM
- **Trust Policy**: WHO can assume IAM roles (you create this)
- **Permission Policy**: WHAT the role can do (AWS managed)
- **Service Account**: Kubernetes identity with AWS powers
- **EBS CSI Driver**: The magic that creates volumes
- **Storage Class**: Template for volume creation
- **PVC/PV Flow**: How requests become actual storage

Each step builds upon the previous one, and the connections between components are clearly explained. You are now a master of EKS Dynamic Storage Provisioning! 🚀

### Quick Reference Commands:
```bash
# Check everything is working
kubectl get storageclass,pv,pvc -A
kubectl get pods -n kube-system | grep ebs-csi
aws ec2 describe-volumes --filters "Name=tag:kubernetes.io/cluster/my-cluster,Values=owned"

# Troubleshoot issues
kubectl describe pvc <pvc-name> -n <namespace>
kubectl logs -n kube-system -l app=ebs-csi-controller
kubectl get events -A --sort-by='.lastTimestamp' | grep -i volume

# OIDC Provider management
aws iam list-open-id-connect-providers
aws eks list-clusters --query "clusters[]" --output text | while read cluster; do
    echo "Cluster: $cluster"
    aws eks describe-cluster --name $cluster --query "cluster.identity.oidc.issuer" --output text
done
```
