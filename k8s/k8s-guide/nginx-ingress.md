# NGINX Ingress Controller Guide for Personal Finance Tracker

## Table of Contents
1. [Overview](#overview)
2. [Why Use NGINX Ingress?](#why-use-nginx-ingress)
3. [Prerequisites](#prerequisites)
4. [Step-by-Step Installation](#step-by-step-installation)
5. [Deploy Simple Ingress Resource](#deploy-simple-ingress-resource)
6. [Testing Without DNS](#testing-without-dns)
7. [Verification Steps](#verification-steps)
8. [Troubleshooting](#troubleshooting)

## Overview

NGINX Ingress Controller is a Kubernetes-native load balancer that manages external access to services in a cluster. It acts as a reverse proxy and provides advanced routing capabilities based on HTTP/HTTPS rules.

### What is an Ingress Controller?

An **Ingress Controller** is a specialized load balancer for Kubernetes that:
- **Routes Traffic**: Directs external traffic to internal services based on rules
- **SSL Termination**: Handles HTTPS certificates and encryption/decryption
- **Load Balancing**: Distributes traffic across multiple backend pods
- **Path-Based Routing**: Routes requests based on URL paths and hostnames
- **Advanced Features**: Rate limiting, authentication, and more

### Request Flow
```
Internet → AWS Load Balancer → NGINX Ingress Controller → Kubernetes Services → Application Pods
```

## Why Use NGINX Ingress?

### Benefits
✅ **Cost Effective**: Single load balancer for multiple services  
✅ **Feature Rich**: Advanced routing, SSL, authentication, rate limiting  
✅ **Kubernetes Native**: Configured using Kubernetes resources  
✅ **High Performance**: NGINX's proven performance and reliability  
✅ **Flexibility**: Extensive customization through annotations  

### Cost Comparison
**Without NGINX Ingress (Multiple ALBs):**
```
Finance App → ALB ($16/month)
Grafana → ALB ($16/month)  
Prometheus → ALB ($16/month)
Total: $48/month + data processing fees
```

**With NGINX Ingress (Single NLB):**
```
All Services → Single NLB ($16/month)
NGINX Controller → Free (runs on your nodes)
Total: $16/month + minimal data processing
```

## Prerequisites

```bash
# Ensure kubectl access to your EKS cluster
kubectl get nodes

# Verify your applications are running
kubectl get pods -n finance-tracker

# Ensure Helm is installed
helm version
```

## Step-by-Step Installation

### 1. Add the NGINX Ingress Helm Repository

```bash
# Add the NGINX Ingress repository
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx

# Update repositories
helm repo update
```

### 2. Install the NGINX Ingress Controller

This will deploy the controller in its own namespace (ingress-nginx), with a LoadBalancer service type so AWS automatically provisions an ELB.

```bash
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace
```

### 3. Verify the Controller is Running

```bash
kubectl get pods -n ingress-nginx
```

You should see one or more pods named `ingress-nginx-controller` in Running status.

### 4. Get the External IP (AWS ELB DNS)

The controller automatically creates a LoadBalancer service:

```bash
kubectl get svc -n ingress-nginx
```

Look for:
```
NAME                                 TYPE           CLUSTER-IP      EXTERNAL-IP                                                              PORT(S)
ingress-nginx-controller             LoadBalancer   10.xxx.xx.xxx   a1234567890abcdef.elb.us-east-1.amazonaws.com   80:xxxx/TCP, 443:xxxx/TCP
```

Use the EXTERNAL-IP to access your ingress routes.

## Deploy Simple Ingress Resource

### 1. Update Your Service to ClusterIP

First, ensure your finance app service is ClusterIP (not NodePort):

```yaml
# finance-app-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: finance-app-service
  namespace: finance-tracker
  labels:
    app: finance-app
spec:
  type: ClusterIP  # Changed from NodePort
  selector:
    app: finance-app
  ports:
  - port: 80
    targetPort: 5000
    protocol: TCP
    name: http
```

Apply the service:
```bash
kubectl apply -f finance-app-service.yaml
```

### 2. Create Simple Ingress Resource

Create a simple ingress resource:

```yaml
# finance-app-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: finance-app-ingress
  namespace: finance-tracker
  annotations:
    kubernetes.io/ingress.class: "nginx"
spec:
  rules:
  - host: finance-app.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: finance-app-service
            port:
              number: 80
```

Apply the ingress:
```bash
kubectl apply -f finance-app-ingress.yaml
```

### 3. Create Enhanced Ingress with Multiple Features

For production use, create an enhanced ingress with additional features:

```yaml
# finance-app-ingress-enhanced.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: finance-app-ingress-enhanced
  namespace: finance-tracker
  annotations:
    # Basic NGINX annotations
    kubernetes.io/ingress.class: "nginx"
    nginx.ingress.kubernetes.io/rewrite-target: /
    
    # File upload size (for receipt uploads)
    nginx.ingress.kubernetes.io/proxy-body-size: "16m"
    
    # Session affinity for better user experience
    nginx.ingress.kubernetes.io/affinity: "cookie"
    nginx.ingress.kubernetes.io/session-cookie-name: "finance-app-session"
    nginx.ingress.kubernetes.io/session-cookie-expires: "86400"
    
    # Rate limiting (100 requests per minute)
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
    
    # Custom headers
    nginx.ingress.kubernetes.io/configuration-snippet: |
      add_header X-App-Name "Personal Finance Tracker" always;
      add_header X-Frame-Options "SAMEORIGIN" always;
      add_header X-Content-Type-Options "nosniff" always;
spec:
  rules:
  - host: finance-app.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: finance-app-service
            port:
              number: 80
```

## Testing Without DNS

### Step 1: Get Load Balancer URL

```bash
# Get the NGINX Ingress Controller Load Balancer URL
LB_URL=$(kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo "Load Balancer URL: $LB_URL"
```

### Step 2: Resolve Load Balancer to IP Address

```bash
# Resolve the Load Balancer hostname to IP addresses
nslookup $LB_URL

# Get all IP addresses
dig +short $LB_URL
```

### Step 3: Update /etc/hosts File

```bash
# Get one of the IP addresses from the previous step
LB_IP="52.12.34.56"  # Replace with actual IP from dig command

# Backup current /etc/hosts
sudo cp /etc/hosts /etc/hosts.backup

# Add entry to /etc/hosts
echo "$LB_IP finance-app.local" | sudo tee -a /etc/hosts

# Verify the entry
tail -1 /etc/hosts
```

### Step 4: Test HTTP Connectivity

```bash
# Test Finance App
curl -v http://finance-app.local/

# Test with specific IP and Host header (alternative method)
curl -v -H "Host: finance-app.local" http://$LB_IP/

# Test health endpoint
curl -H "Host: finance-app.local" http://finance-app.local/health
```

### Step 5: Browser Testing

1. **Open your browser**
2. **Navigate to**: `http://finance-app.local`
3. **You should see**: Your Personal Finance Tracker application

## Verification Steps

### 1. Check All Components

```bash
# Check NGINX Ingress Controller pods
kubectl get pods -n ingress-nginx

# Check services
kubectl get svc -n ingress-nginx

# Check ingress resources
kubectl get ingress -A

# Check your application
kubectl get pods -n finance-tracker
kubectl get svc -n finance-tracker
```

### 2. Verify Ingress Configuration

```bash
# Describe ingress resource
kubectl describe ingress finance-app-ingress -n finance-tracker

# Check if ingress has an address
kubectl get ingress finance-app-ingress -n finance-tracker
```

Expected output:
```
NAME                  CLASS    HOSTS                ADDRESS                                                                   PORTS   AGE
finance-app-ingress   <none>   finance-app.local    a1234567890abcdef.elb.us-east-1.amazonaws.com                        80      5m
```

### 3. Test Backend Connectivity

```bash
# Test backend service directly
kubectl port-forward -n finance-tracker svc/finance-app-service 8080:80 &
curl http://localhost:8080/
```

### 4. Check NGINX Configuration

```bash
# View NGINX configuration (optional)
kubectl exec -n ingress-nginx deployment/ingress-nginx-controller -- cat /etc/nginx/nginx.conf | grep -A 10 -B 10 "finance-app"
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Load Balancer Stuck in Pending

**Symptoms:**
```bash
kubectl get svc -n ingress-nginx
# EXTERNAL-IP shows <pending>
```

**Solutions:**
```bash
# Check AWS Load Balancer Controller
kubectl get pods -n kube-system | grep aws-load-balancer

# Check service events
kubectl describe svc -n ingress-nginx ingress-nginx-controller

# Verify AWS permissions for EKS cluster
```

#### 2. 404 Not Found Errors

**Symptoms:**
- Browser shows 404 error
- `curl` returns 404

**Solutions:**
```bash
# Check if ingress resource exists
kubectl get ingress -n finance-tracker

# Verify service name matches
kubectl get svc -n finance-tracker finance-app-service

# Check service endpoints
kubectl get endpoints -n finance-tracker finance-app-service

# Test backend service directly
kubectl port-forward -n finance-tracker svc/finance-app-service 8080:80 &
curl http://localhost:8080/
```

#### 3. DNS Resolution Issues

**Symptoms:**
- `nslookup finance-app.local` fails
- Browser can't resolve hostname

**Solutions:**
```bash
# Check /etc/hosts entry
grep "finance-app.local" /etc/hosts

# Ensure correct IP address
LB_IP=$(dig +short $LB_URL | head -1)
echo "$LB_IP finance-app.local" | sudo tee -a /etc/hosts

# Test with curl using IP and Host header
curl -H "Host: finance-app.local" http://$LB_IP/
```

#### 4. NGINX Controller Not Starting

**Symptoms:**
```bash
kubectl get pods -n ingress-nginx
# Pod shows CrashLoopBackOff or Error
```

**Solutions:**
```bash
# Check controller logs
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller

# Check events
kubectl get events -n ingress-nginx --sort-by='.lastTimestamp'

# Reinstall if necessary
helm uninstall ingress-nginx -n ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx --namespace ingress-nginx --create-namespace
```

### Health Check Script

Create a simple health check script:

```bash
#!/bin/bash
# nginx-health-check.sh

echo "=== NGINX Ingress Health Check ==="

# 1. Check pods
echo "1. Checking NGINX Ingress Controller pods..."
kubectl get pods -n ingress-nginx

# 2. Check services
echo "2. Checking services..."
kubectl get svc -n ingress-nginx

# 3. Check ingress resources
echo "3. Checking ingress resources..."
kubectl get ingress -A

# 4. Test connectivity
echo "4. Testing connectivity..."
LB_URL=$(kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
if [ ! -z "$LB_URL" ]; then
    echo "Load Balancer URL: $LB_URL"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -H "Host: finance-app.local" http://$LB_URL/ || echo "000")
    echo "HTTP Response Code: $HTTP_CODE"
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ Finance App is accessible"
    else
        echo "❌ Finance App returned HTTP $HTTP_CODE"
    fi
else
    echo "❌ Load Balancer not ready"
fi

echo "=== Health Check Complete ==="
```

Make it executable and run:
```bash
chmod +x nginx-health-check.sh
./nginx-health-check.sh
```

## Key Notes

✅ **Yes, this will create an AWS Load Balancer automatically** (via LoadBalancer service type on ingress-nginx)

✅ **Single Load Balancer for multiple services** - Cost effective approach

✅ **Advanced routing capabilities** - Path-based, host-based, and header-based routing

✅ **Production ready** - Includes rate limiting, session affinity, and security headers

To verify ingress is working properly, run:
```bash
kubectl describe ingress finance-app-ingress -n finance-tracker
```

This simplified guide focuses on the essential steps to get NGINX Ingress Controller running with your Personal Finance Tracker application, without overwhelming complexity.
