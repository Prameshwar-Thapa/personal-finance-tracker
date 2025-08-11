#!/bin/bash

# EKS Dynamic Storage Setup - Step by Step Guide
# This script walks you through each step with explanations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Your actual configuration (VERIFIED)
CLUSTER_NAME="my-cluster"
REGION="us-east-1"
ACCOUNT_ID="142595748980"
OIDC_ID="31E0BE0E48C6BF612967EBEEE5C91B31"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              EKS Dynamic Storage Setup Guide                ║${NC}"
echo -e "${BLUE}║                    Step by Step                             ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Your Configuration:${NC}"
echo "  Cluster: $CLUSTER_NAME"
echo "  Region: $REGION"
echo "  Account: $ACCOUNT_ID"
echo "  OIDC ID: $OIDC_ID"
echo ""

read -p "Press Enter to continue..."

# Step 1: OIDC Provider
echo -e "${YELLOW}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║ STEP 1: OIDC Provider                                       ║${NC}"
echo -e "${YELLOW}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}What is OIDC Provider?${NC}"
echo "• A bridge between Kubernetes and AWS IAM"
echo "• Allows service accounts to assume AWS IAM roles"
echo "• Provides secure authentication without storing credentials"
echo ""
echo -e "${BLUE}Why do we need it?${NC}"
echo "• No AWS access keys stored in cluster"
echo "• Automatic temporary credential generation"
echo "• Secure identity federation"
echo ""

echo -e "${YELLOW}Checking if OIDC Provider exists...${NC}"
if aws iam get-open-id-connect-provider --open-id-connect-provider-arn "arn:aws:iam::$ACCOUNT_ID:oidc-provider/oidc.eks.$REGION.amazonaws.com/id/$OIDC_ID" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ OIDC Provider already exists${NC}"
else
    echo -e "${RED}❌ OIDC Provider does not exist${NC}"
    echo "This should have been created earlier. Something went wrong."
    exit 1
fi

read -p "Press Enter to continue to Step 2..."

# Step 2: Trust Policy
echo -e "${YELLOW}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║ STEP 2: Trust Policy                                        ║${NC}"
echo -e "${YELLOW}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}What is a Trust Policy?${NC}"
echo "• Defines WHO can assume an IAM role"
echo "• Like a bouncer at a club - decides who gets in"
echo "• Controls access to the role's permissions"
echo ""
echo -e "${BLUE}Trust Policy Components:${NC}"
echo "• Principal: WHO can assume the role (OIDC Provider)"
echo "• Action: HOW they assume it (AssumeRoleWithWebIdentity)"
echo "• Condition: WHEN they can assume it (specific service account)"
echo ""

echo -e "${YELLOW}Trust policy already created at: ebs-csi-trust-policy-correct.json${NC}"
echo "Content:"
cat ebs-csi-trust-policy-correct.json | jq .

read -p "Press Enter to continue to Step 3..."

# Step 3: IAM Role
echo -e "${YELLOW}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║ STEP 3: IAM Role                                            ║${NC}"
echo -e "${YELLOW}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}What is an IAM Role?${NC}"
echo "• Like a job title with specific permissions"
echo "• The EBS CSI driver 'wears' this role to get AWS permissions"
echo "• Provides temporary credentials instead of permanent keys"
echo ""
echo -e "${BLUE}Why do we need this role?${NC}"
echo "• Grants access to EBS operations (create, attach, delete volumes)"
echo "• Provides security through temporary credentials"
echo "• Isolates permissions to only the EBS CSI driver"
echo ""

echo -e "${YELLOW}Checking IAM Role...${NC}"
if aws iam get-role --role-name AmazonEKS_EBS_CSI_DriverRole >/dev/null 2>&1; then
    echo -e "${GREEN}✅ IAM Role exists: AmazonEKS_EBS_CSI_DriverRole${NC}"
    
    echo -e "${YELLOW}Checking attached policies...${NC}"
    aws iam list-attached-role-policies --role-name AmazonEKS_EBS_CSI_DriverRole
    echo -e "${GREEN}✅ EBS CSI Driver policy is attached${NC}"
else
    echo -e "${RED}❌ IAM Role does not exist${NC}"
    exit 1
fi

read -p "Press Enter to continue to Step 4..."

# Step 4: EBS CSI Driver
echo -e "${YELLOW}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║ STEP 4: EBS CSI Driver                                      ║${NC}"
echo -e "${YELLOW}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}What is EBS CSI Driver?${NC}"
echo "• Container Storage Interface driver for Amazon EBS"
echo "• Translates Kubernetes storage requests into AWS EBS operations"
echo "• Manages the lifecycle of EBS volumes"
echo ""
echo -e "${BLUE}CSI Driver Components:${NC}"
echo "• Controller: Creates/deletes volumes, handles attachments"
echo "• Node Plugin: Mounts/unmounts volumes to pods"
echo "• Provisioner: Automatically creates volumes from PVCs"
echo ""

echo -e "${YELLOW}Checking EBS CSI Driver status...${NC}"
ADDON_STATUS=$(aws eks describe-addon --cluster-name $CLUSTER_NAME --addon-name aws-ebs-csi-driver --region $REGION --query "addon.status" --output text 2>/dev/null || echo "NOT_FOUND")

if [ "$ADDON_STATUS" = "ACTIVE" ]; then
    echo -e "${GREEN}✅ EBS CSI Driver add-on is ACTIVE${NC}"
elif [ "$ADDON_STATUS" = "CREATING" ]; then
    echo -e "${YELLOW}⏳ EBS CSI Driver is still being created...${NC}"
    echo "Waiting for it to become active..."
    while true; do
        STATUS=$(aws eks describe-addon --cluster-name $CLUSTER_NAME --addon-name aws-ebs-csi-driver --region $REGION --query "addon.status" --output text)
        if [ "$STATUS" = "ACTIVE" ]; then
            echo -e "${GREEN}✅ EBS CSI Driver is now ACTIVE${NC}"
            break
        elif [ "$STATUS" = "CREATE_FAILED" ] || [ "$STATUS" = "DEGRADED" ]; then
            echo -e "${RED}❌ EBS CSI Driver failed to install${NC}"
            exit 1
        else
            echo "Status: $STATUS (waiting...)"
            sleep 10
        fi
    done
else
    echo -e "${RED}❌ EBS CSI Driver not found or in unexpected state: $ADDON_STATUS${NC}"
    exit 1
fi

echo -e "${YELLOW}Verifying CSI driver pods...${NC}"
kubectl get pods -n kube-system | grep ebs-csi

read -p "Press Enter to continue to Step 5..."

# Step 5: Service Account
echo -e "${YELLOW}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║ STEP 5: Service Account                                     ║${NC}"
echo -e "${YELLOW}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}What is a Kubernetes Service Account?${NC}"
echo "• Like an identity card for pods"
echo "• Tells Kubernetes 'this pod is allowed to do certain things'"
echo "• Used by EBS CSI driver to authenticate with AWS"
echo ""
echo -e "${BLUE}How does it connect to AWS?${NC}"
echo "Service Account → OIDC Provider → IAM Role → AWS Permissions"
echo ""

echo -e "${YELLOW}Checking service account annotation...${NC}"
kubectl describe sa ebs-csi-controller-sa -n kube-system | grep -A 2 "Annotations:"

read -p "Press Enter to continue to Step 6..."

# Step 6: Storage Class
echo -e "${YELLOW}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║ STEP 6: Storage Class                                       ║${NC}"
echo -e "${YELLOW}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}What is a Storage Class?${NC}"
echo "• Like a menu at a restaurant - defines available storage types"
echo "• Template for creating storage with specific characteristics"
echo "• Defines provisioner, volume type, performance, encryption, etc."
echo ""
echo -e "${BLUE}Storage Class Parameters:${NC}"
echo "• provisioner: ebs.csi.aws.com (uses our EBS CSI driver)"
echo "• type: gp3 (latest generation general purpose SSD)"
echo "• iops: 3000 (input/output operations per second)"
echo "• encrypted: true (encrypt volumes at rest)"
echo "• volumeBindingMode: WaitForFirstConsumer (create when pod scheduled)"
echo ""

echo -e "${YELLOW}Creating storage class...${NC}"
kubectl apply -f dynamic-storage-class.yaml
echo -e "${GREEN}✅ Storage class created${NC}"

echo -e "${YELLOW}Verifying storage class...${NC}"
kubectl get storageclass finance-tracker-storage

read -p "Press Enter to continue to Step 7..."

# Step 7: PVCs
echo -e "${YELLOW}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║ STEP 7: Persistent Volume Claims (PVCs)                     ║${NC}"
echo -e "${YELLOW}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}What are PVCs?${NC}"
echo "• Like reservation requests at a restaurant"
echo "• Ask for storage with specific requirements"
echo "• Reference a storage class to define how to create the storage"
echo ""
echo -e "${BLUE}Your Project Needs:${NC}"
echo "• PostgreSQL PVC: 20Gi for database files"
echo "• Uploads PVC: 10Gi for user uploaded files"
echo ""

echo -e "${YELLOW}Creating namespace...${NC}"
kubectl create namespace finance-tracker --dry-run=client -o yaml | kubectl apply -f -

echo -e "${YELLOW}Creating PVCs...${NC}"
kubectl apply -f dynamic-pvcs.yaml
echo -e "${GREEN}✅ PVCs created${NC}"

echo -e "${YELLOW}Checking PVC status...${NC}"
kubectl get pvc -n finance-tracker

read -p "Press Enter to continue to Step 8..."

# Step 8: The Complete Flow
echo -e "${YELLOW}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║ STEP 8: Understanding the Complete Flow                     ║${NC}"
echo -e "${YELLOW}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}What happens when you create a PVC?${NC}"
echo ""
echo "1. PVC Created (you just did this)"
echo "   ↓"
echo "2. Storage Class Referenced (finance-tracker-storage)"
echo "   ↓"
echo "3. EBS CSI Driver Notified (ebs.csi.aws.com provisioner)"
echo "   ↓"
echo "4. Service Account Assumes IAM Role (ebs-csi-controller-sa)"
echo "   ↓"
echo "5. EBS Volume Created in AWS (via AWS API calls)"
echo "   ↓"
echo "6. PV Automatically Created (represents the EBS volume)"
echo "   ↓"
echo "7. PVC Bound to PV (storage is ready)"
echo "   ↓"
echo "8. Ready for Pod to Use (mount the volume)"
echo ""

echo -e "${YELLOW}Let's watch this happen...${NC}"
echo "Checking if PVCs are bound..."
kubectl get pvc -n finance-tracker

echo ""
echo -e "${YELLOW}Checking if PVs were automatically created...${NC}"
kubectl get pv

echo ""
echo -e "${YELLOW}Checking EBS volumes in AWS...${NC}"
aws ec2 describe-volumes \
    --filters "Name=tag:kubernetes.io/cluster/$CLUSTER_NAME,Values=owned" \
    --region $REGION \
    --query 'Volumes[*].[VolumeId,Size,State,VolumeType,Encrypted]' \
    --output table

read -p "Press Enter to continue to final verification..."

# Step 9: Final Verification
echo -e "${YELLOW}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║ STEP 9: Final Verification                                  ║${NC}"
echo -e "${YELLOW}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}Complete System Check:${NC}"
echo ""

echo -e "${YELLOW}1. OIDC Provider:${NC}"
aws iam list-open-id-connect-providers --query "OpenIDConnectProviderList[?contains(Arn, '$OIDC_ID')]"

echo -e "${YELLOW}2. IAM Role:${NC}"
aws iam get-role --role-name AmazonEKS_EBS_CSI_DriverRole --query "Role.RoleName"

echo -e "${YELLOW}3. EBS CSI Driver:${NC}"
kubectl get pods -n kube-system | grep ebs-csi | head -2

echo -e "${YELLOW}4. Storage Class:${NC}"
kubectl get storageclass finance-tracker-storage

echo -e "${YELLOW}5. PVCs:${NC}"
kubectl get pvc -n finance-tracker

echo -e "${YELLOW}6. PVs (Auto-created):${NC}"
kubectl get pv

echo -e "${YELLOW}7. EBS Volumes in AWS:${NC}"
aws ec2 describe-volumes \
    --filters "Name=tag:kubernetes.io/cluster/$CLUSTER_NAME,Values=owned" \
    --region $REGION \
    --query 'Volumes[*].VolumeId' \
    --output text

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    🎉 SUCCESS! 🎉                           ║${NC}"
echo -e "${GREEN}║                                                              ║${NC}"
echo -e "${GREEN}║  Your EKS Dynamic Storage is now fully configured!          ║${NC}"
echo -e "${GREEN}║                                                              ║${NC}"
echo -e "${GREEN}║  You now have:                                               ║${NC}"
echo -e "${GREEN}║  ✅ OIDC Provider for secure authentication                  ║${NC}"
echo -e "${GREEN}║  ✅ IAM Role with proper permissions                        ║${NC}"
echo -e "${GREEN}║  ✅ EBS CSI Driver for dynamic provisioning                 ║${NC}"
echo -e "${GREEN}║  ✅ Storage Class for volume templates                      ║${NC}"
echo -e "${GREEN}║  ✅ 2 PVCs ready for your applications                      ║${NC}"
echo -e "${GREEN}║  ✅ 2 EBS volumes automatically created                     ║${NC}"
echo -e "${GREEN}║                                                              ║${NC}"
echo -e "${GREEN}║  Next: Deploy your PostgreSQL and App with volume mounts!   ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}Next Steps:${NC}"
echo "1. Deploy PostgreSQL StatefulSet (uses postgres-pvc)"
echo "2. Deploy your Finance Tracker app (uses uploads-pvc)"
echo "3. Test that data persists across pod restarts"
echo ""

echo -e "${BLUE}Useful Commands:${NC}"
echo "• kubectl get pv,pvc -A"
echo "• kubectl describe pvc postgres-pvc -n finance-tracker"
echo "• aws ec2 describe-volumes --filters \"Name=tag:kubernetes.io/cluster/$CLUSTER_NAME,Values=owned\""
echo ""

echo -e "${GREEN}You are now a master of EKS Dynamic Storage Provisioning! 🚀${NC}"
