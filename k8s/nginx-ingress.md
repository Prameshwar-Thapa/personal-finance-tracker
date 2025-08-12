# NGINX Ingress Controller Guide for Personal Finance Tracker

## Table of Contents
1. [Overview](#overview)
2. [NGINX Ingress vs AWS ELB](#nginx-ingress-vs-aws-elb)
3. [How NGINX Ingress Works](#how-nginx-ingress-works)
4. [Architecture](#architecture)
5. [Prerequisites](#prerequisites)
6. [Installation Methods](#installation-methods)
7. [Step-by-Step Installation](#step-by-step-installation)
8. [Configuration for Finance Tracker](#configuration-for-finance-tracker)
9. [Testing Without DNS](#testing-without-dns)
10. [Advanced Features](#advanced-features)
11. [Troubleshooting](#troubleshooting)
12. [Interview Questions](#interview-questions)

## Overview

NGINX Ingress Controller is a Kubernetes-native load balancer that manages external access to services in a cluster. It acts as a reverse proxy, load balancer, and SSL termination point, providing advanced routing capabilities based on HTTP/HTTPS rules.

### What is an Ingress Controller?

An **Ingress Controller** is a specialized load balancer for Kubernetes environments that:
- **Routes Traffic**: Directs external traffic to internal services based on rules
- **SSL Termination**: Handles HTTPS certificates and encryption/decryption
- **Load Balancing**: Distributes traffic across multiple backend pods
- **Path-Based Routing**: Routes requests based on URL paths and hostnames
- **Advanced Features**: Rate limiting, authentication, caching, and more

### Why Use NGINX Ingress?

1. **Cost Effective**: Single load balancer for multiple services
2. **Feature Rich**: Advanced routing, SSL, authentication, rate limiting
3. **Kubernetes Native**: Configured using Kubernetes resources
4. **High Performance**: NGINX's proven performance and reliability
5. **Flexibility**: Extensive customization through annotations and ConfigMaps

## NGINX Ingress vs AWS ELB

### Comparison Table

| Feature | NGINX Ingress | AWS ELB (ALB/NLB) |
|---------|---------------|-------------------|
| **Cost** | Single LB for multiple services | One LB per service |
| **Layer 7 Features** | Full HTTP/HTTPS routing | Limited HTTP features |
| **SSL Management** | cert-manager integration | AWS Certificate Manager |
| **Path-based Routing** | Advanced regex support | Basic path matching |
| **Rate Limiting** | Built-in with annotations | Requires WAF |
| **Authentication** | Multiple auth methods | Cognito/OIDC only |
| **Caching** | Built-in caching | CloudFront required |
| **WebSocket Support** | Native support | Limited support |
| **Custom Headers** | Full control | Limited options |
| **Monitoring** | Prometheus metrics | CloudWatch only |

### When to Use NGINX Ingress

✅ **Use NGINX Ingress when:**
- You have multiple services needing external access
- You need advanced routing (regex, rewrite rules)
- You want cost optimization (single LB)
- You need features like rate limiting, auth, caching
- You want Kubernetes-native configuration
- You need WebSocket or gRPC support

❌ **Use AWS ELB when:**
- You have simple routing requirements
- You prefer AWS-managed services
- You need deep AWS integration (WAF, Shield)
- You have compliance requirements for AWS services

### Cost Comparison Example

**AWS ELB Approach:**
```
Finance App Service → ALB ($16/month)
Monitoring (Grafana) → ALB ($16/month)
API Service → ALB ($16/month)
Total: $48/month + data processing fees
```

**NGINX Ingress Approach:**
```
All Services → Single NLB ($16/month)
NGINX Ingress Controller → Free (runs on your nodes)
Total: $16/month + minimal data processing
```

## How NGINX Ingress Works

### Architecture Flow

```
Internet
    ↓
AWS Load Balancer (NLB/ALB)
    ↓
NGINX Ingress Controller Pod
    ↓
Kubernetes Services
    ↓
Application Pods
```

### Detailed Request Flow

1. **External Request**: Client makes HTTP/HTTPS request
2. **AWS Load Balancer**: Routes to NGINX Ingress Controller
3. **Ingress Controller**: 
   - Reads Ingress resources
   - Applies routing rules
   - Performs SSL termination
   - Adds custom headers
   - Applies rate limiting/auth
4. **Service Routing**: Forwards to appropriate Kubernetes service
5. **Pod Selection**: Service routes to healthy backend pods
6. **Response**: Response flows back through the same path

### Components Explained

#### 1. NGINX Ingress Controller
- **Pod**: Runs NGINX with custom Kubernetes integration
- **ConfigMap**: Global NGINX configuration
- **Service**: Exposes controller to external load balancer
- **RBAC**: Permissions to read Ingress resources

#### 2. Ingress Resources
- **Rules**: Define routing logic (host, path, backend)
- **Annotations**: NGINX-specific configurations
- **TLS**: SSL certificate configuration

#### 3. Backend Services
- **ClusterIP Services**: Internal services that Ingress routes to
- **Endpoints**: Actual pod IPs that services point to

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Internet Traffic                         │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                AWS Network Load Balancer                    │
│            (Single entry point - Cost effective)           │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│              NGINX Ingress Controller Pod                   │
│  ┌─────────────────┬─────────────────┬─────────────────┐    │
│  │   SSL Term.     │   Routing       │   Load Balancing│    │
│  │   Rate Limit    │   Auth          │   Caching       │    │
│  └─────────────────┴─────────────────┴─────────────────┘    │
└─────┬─────────────┬─────────────┬─────────────┬─────────────┘
      │             │             │             │
┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐
│Finance App│ │  Grafana  │ │Prometheus │ │   API     │
│ Service   │ │  Service  │ │ Service   │ │ Service   │
└─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────┬─────┘
      │             │             │             │
┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐
│   Pods    │ │   Pods    │ │   Pods    │ │   Pods    │
└───────────┘ └───────────┘ └───────────┘ └───────────┘
```

### Request Routing Example

```
finance-app.local/dashboard → Finance App Service
finance-app.local/api/v1    → API Service  
grafana.local              → Grafana Service
prometheus.local           → Prometheus Service
```

## Prerequisites

```bash
# Ensure you have kubectl access to your EKS cluster
kubectl get nodes

# Verify your applications are running
kubectl get pods -n finance-tracker
kubectl get pods -n monitoring

# Check current services
kubectl get svc -n finance-tracker
kubectl get svc -n monitoring

# Ensure you have Helm installed
helm version
```

## Installation Methods

### Method 1: Helm Installation (Recommended)

**Advantages:**
- Easy installation and upgrades
- Customizable values
- Production-ready defaults
- Community maintained

### Method 2: YAML Manifests

**Advantages:**
- Full control over configuration
- No Helm dependency
- Easier to understand for learning

### Method 3: AWS Load Balancer Controller + NGINX

**Advantages:**
- Best AWS integration
- Advanced AWS features
- Automatic security group management

## Step-by-Step Installation

### Method 1: Helm Installation (Recommended)

#### Step 1: Add NGINX Ingress Helm Repository

```bash
# Add the NGINX Ingress repository
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx

# Update repositories
helm repo update

# Search for available charts
helm search repo ingress-nginx
```

#### Step 2: Create Custom Values File

**File: `/home/prameshwar/Desktop/k8s/nginx-ingress-values.yaml`**
```yaml
# NGINX Ingress Controller configuration
controller:
  # Replica count for high availability
  replicaCount: 2
  
  # Service configuration
  service:
    # Use Network Load Balancer for better performance
    type: LoadBalancer
    annotations:
      # AWS-specific annotations
      service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
      service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"
      service.beta.kubernetes.io/aws-load-balancer-backend-protocol: "tcp"
      # Optional: Use internal load balancer
      # service.beta.kubernetes.io/aws-load-balancer-internal: "true"
    
    # External traffic policy for better performance
    externalTrafficPolicy: Local
    
    # Ports configuration
    ports:
      http: 80
      https: 443
    
    # Target ports
    targetPorts:
      http: http
      https: https

  # Resource limits
  resources:
    requests:
      cpu: 100m
      memory: 90Mi
    limits:
      cpu: 500m
      memory: 500Mi

  # Node selector (optional - run on specific nodes)
  # nodeSelector:
  #   kubernetes.io/os: linux

  # Tolerations for running on all nodes
  tolerations: []

  # Affinity rules for pod placement
  affinity:
    podAntiAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchExpressions:
            - key: app.kubernetes.io/name
              operator: In
              values:
              - ingress-nginx
          topologyKey: kubernetes.io/hostname

  # NGINX configuration
  config:
    # Global settings
    use-forwarded-headers: "true"
    compute-full-forwarded-for: "true"
    use-proxy-protocol: "false"
    
    # Performance tuning
    worker-processes: "auto"
    worker-connections: "1024"
    
    # Logging
    log-format-upstream: '$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent" $request_length $request_time [$proxy_upstream_name] [$proxy_alternative_upstream_name] $upstream_addr $upstream_response_length $upstream_response_time $upstream_status $req_id'
    
    # Security headers
    add-headers: "ingress-nginx/custom-headers"
    
    # Rate limiting (optional)
    # rate-limit: "100"
    # rate-limit-window: "1m"

  # Metrics configuration
  metrics:
    enabled: true
    service:
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "10254"
    serviceMonitor:
      enabled: false  # Set to true if you have Prometheus Operator

  # Admission webhooks
  admissionWebhooks:
    enabled: true
    failurePolicy: Fail
    port: 8443

# Default backend (optional)
defaultBackend:
  enabled: true
  image:
    repository: k8s.gcr.io/defaultbackend-amd64
    tag: "1.5"
  resources:
    requests:
      cpu: 10m
      memory: 20Mi
    limits:
      cpu: 20m
      memory: 30Mi

# RBAC configuration
rbac:
  create: true
  scope: false

# Service account
serviceAccount:
  create: true
  name: ""
  annotations: {}

# Pod security policy
podSecurityPolicy:
  enabled: false
```

#### Step 3: Create Custom Headers ConfigMap (Optional)

**File: `/home/prameshwar/Desktop/k8s/nginx-custom-headers.yaml`**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: custom-headers
  namespace: ingress-nginx
data:
  X-Frame-Options: "SAMEORIGIN"
  X-Content-Type-Options: "nosniff"
  X-XSS-Protection: "1; mode=block"
  Referrer-Policy: "strict-origin-when-cross-origin"
  Content-Security-Policy: "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; font-src 'self' https://cdnjs.cloudflare.com; img-src 'self' data: https:;"
```

#### Step 4: Install NGINX Ingress Controller

```bash
# Create ingress-nginx namespace
kubectl create namespace ingress-nginx

# Apply custom headers (optional)
kubectl apply -f /home/prameshwar/Desktop/k8s/nginx-custom-headers.yaml

# Install NGINX Ingress using Helm
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --values /home/prameshwar/Desktop/k8s/nginx-ingress-values.yaml \
  --wait \
  --timeout 300s

# Verify installation
helm list -n ingress-nginx
```

#### Step 5: Verify Installation

```bash
# Check if pods are running
kubectl get pods -n ingress-nginx

# Expected output:
# NAME                                        READY   STATUS    RESTARTS   AGE
# ingress-nginx-controller-xxx-xxx            1/1     Running   0          2m
# ingress-nginx-controller-xxx-yyy            1/1     Running   0          2m
# ingress-nginx-defaultbackend-xxx-xxx        1/1     Running   0          2m

# Check service and get Load Balancer URL
kubectl get svc -n ingress-nginx

# Expected output:
# NAME                                 TYPE           CLUSTER-IP      EXTERNAL-IP                                                               PORT(S)                      AGE
# ingress-nginx-controller             LoadBalancer   10.100.xxx.xxx  a1b2c3d4e5f6g7h8-1234567890.us-east-1.elb.amazonaws.com                80:32080/TCP,443:32443/TCP   2m
# ingress-nginx-controller-admission   ClusterIP      10.100.xxx.xxx  <none>                                                                    443/TCP                      2m
# ingress-nginx-defaultbackend         ClusterIP      10.100.xxx.xxx  <none>                                                                    80/TCP                       2m
```

### Method 2: YAML Manifests Installation

If you prefer not to use Helm:

```bash
# Install using official YAML manifests
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/aws/deploy.yaml

# Wait for deployment
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s
```

## Configuration for Finance Tracker

### Step 1: Update Services to ClusterIP

Your current services might be NodePort. For Ingress to work properly, change them to ClusterIP:

**File: `/home/prameshwar/Desktop/k8s/finance-app-service-clusterip.yaml`**
```yaml
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

**File: `/home/prameshwar/Desktop/k8s/monitoring-services-clusterip.yaml`**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: grafana-service
  namespace: monitoring
  labels:
    app.kubernetes.io/name: grafana
spec:
  type: ClusterIP
  selector:
    app.kubernetes.io/name: grafana
  ports:
  - port: 80
    targetPort: 3000
    protocol: TCP
    name: http
---
apiVersion: v1
kind: Service
metadata:
  name: prometheus-service
  namespace: monitoring
  labels:
    app.kubernetes.io/name: prometheus
spec:
  type: ClusterIP
  selector:
    app.kubernetes.io/name: prometheus
  ports:
  - port: 80
    targetPort: 9090
    protocol: TCP
    name: http
```

### Step 2: Create Ingress Resources

**File: `/home/prameshwar/Desktop/k8s/finance-tracker-ingress.yaml`**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: finance-tracker-ingress
  namespace: finance-tracker
  annotations:
    # Basic NGINX annotations
    kubernetes.io/ingress.class: "nginx"
    nginx.ingress.kubernetes.io/rewrite-target: /
    
    # SSL and security
    nginx.ingress.kubernetes.io/ssl-redirect: "false"  # Set to true in production
    nginx.ingress.kubernetes.io/force-ssl-redirect: "false"
    
    # File upload size (for receipt uploads)
    nginx.ingress.kubernetes.io/proxy-body-size: "16m"
    
    # Session affinity for better user experience
    nginx.ingress.kubernetes.io/affinity: "cookie"
    nginx.ingress.kubernetes.io/session-cookie-name: "finance-app-session"
    nginx.ingress.kubernetes.io/session-cookie-expires: "86400"
    nginx.ingress.kubernetes.io/session-cookie-max-age: "86400"
    nginx.ingress.kubernetes.io/session-cookie-path: "/"
    
    # Rate limiting (optional)
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
    
    # Custom headers
    nginx.ingress.kubernetes.io/configuration-snippet: |
      add_header X-App-Name "Personal Finance Tracker" always;
      add_header X-App-Version "1.0" always;
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
  # Uncomment for HTTPS
  # tls:
  # - hosts:
  #   - finance-app.local
  #   secretName: finance-app-tls
```

**File: `/home/prameshwar/Desktop/k8s/monitoring-ingress.yaml`**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: monitoring-ingress
  namespace: monitoring
  annotations:
    kubernetes.io/ingress.class: "nginx"
    nginx.ingress.kubernetes.io/rewrite-target: /
    
    # Authentication (optional - for production)
    # nginx.ingress.kubernetes.io/auth-type: basic
    # nginx.ingress.kubernetes.io/auth-secret: basic-auth
    # nginx.ingress.kubernetes.io/auth-realm: 'Authentication Required - Monitoring'
    
    # Rate limiting for monitoring tools
    nginx.ingress.kubernetes.io/rate-limit: "50"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
spec:
  rules:
  - host: grafana.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: prometheus-stack-grafana  # Use actual Grafana service name
            port:
              number: 80
  - host: prometheus.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: prometheus-stack-kube-prom-prometheus  # Use actual Prometheus service name
            port:
              number: 9090
```

### Step 3: Advanced Ingress with Path-based Routing

**File: `/home/prameshwar/Desktop/k8s/advanced-ingress.yaml`**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: finance-app-advanced-ingress
  namespace: finance-tracker
  annotations:
    kubernetes.io/ingress.class: "nginx"
    nginx.ingress.kubernetes.io/rewrite-target: /$2
    nginx.ingress.kubernetes.io/proxy-body-size: "16m"
    nginx.ingress.kubernetes.io/affinity: "cookie"
    
    # Custom error pages
    nginx.ingress.kubernetes.io/custom-http-errors: "404,503"
    nginx.ingress.kubernetes.io/default-backend: "default-http-backend"
    
    # CORS configuration
    nginx.ingress.kubernetes.io/enable-cors: "true"
    nginx.ingress.kubernetes.io/cors-allow-methods: "GET, POST, PUT, DELETE, OPTIONS"
    nginx.ingress.kubernetes.io/cors-allow-headers: "DNT,X-CustomHeader,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Authorization"
    
    # Caching for static assets
    nginx.ingress.kubernetes.io/configuration-snippet: |
      location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
      }
spec:
  rules:
  - host: finance-app.local
    http:
      paths:
      # Main application
      - path: /app(/|$)(.*)
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
      
      # Static files
      - path: /static(/|$)(.*)
        pathType: Prefix
        backend:
          service:
            name: finance-app-service
            port:
              number: 80
      
      # Health check
      - path: /health
        pathType: Exact
        backend:
          service:
            name: finance-app-service
            port:
              number: 80
      
      # Metrics endpoint
      - path: /metrics
        pathType: Exact
        backend:
          service:
            name: finance-app-service
            port:
              number: 80
  
  # Monitoring tools on same domain
  - host: finance-app.local
    http:
      paths:
      - path: /grafana(/|$)(.*)
        pathType: Prefix
        backend:
          service:
            name: prometheus-stack-grafana
            port:
              number: 80
      
      - path: /prometheus(/|$)(.*)
        pathType: Prefix
        backend:
          service:
            name: prometheus-stack-kube-prom-prometheus
            port:
              number: 9090
```

### Step 4: Deploy Ingress Resources

```bash
# Apply ClusterIP services first
kubectl apply -f /home/prameshwar/Desktop/k8s/finance-app-service-clusterip.yaml
kubectl apply -f /home/prameshwar/Desktop/k8s/monitoring-services-clusterip.yaml

# Apply Ingress resources
kubectl apply -f /home/prameshwar/Desktop/k8s/finance-tracker-ingress.yaml
kubectl apply -f /home/prameshwar/Desktop/k8s/monitoring-ingress.yaml

# Verify Ingress resources
kubectl get ingress -A

# Check Ingress details
kubectl describe ingress finance-tracker-ingress -n finance-tracker
kubectl describe ingress monitoring-ingress -n monitoring
```
## Testing Without DNS

### Step 1: Get Load Balancer URL

```bash
# Get the NGINX Ingress Controller Load Balancer URL
LB_URL=$(kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo "Load Balancer URL: $LB_URL"

# If hostname is not available, get IP
if [ -z "$LB_URL" ]; then
    LB_IP=$(kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    echo "Load Balancer IP: $LB_IP"
fi
```

### Step 2: Resolve Load Balancer to IP Address

```bash
# Resolve the Load Balancer hostname to IP addresses
nslookup $LB_URL

# Example output:
# Server:    127.0.0.53
# Address:   127.0.0.53#53
# 
# Non-authoritative answer:
# Name:   a1b2c3d4e5f6g7h8-1234567890.us-east-1.elb.amazonaws.com
# Address: 52.12.34.56
# Name:   a1b2c3d4e5f6g7h8-1234567890.us-east-1.elb.amazonaws.com
# Address: 18.45.67.89

# Get all IP addresses
dig +short $LB_URL
```

### Step 3: Update /etc/hosts File

```bash
# Get one of the IP addresses from the previous step
LB_IP="52.12.34.56"  # Replace with actual IP

# Backup current /etc/hosts
sudo cp /etc/hosts /etc/hosts.backup

# Add entries to /etc/hosts
sudo tee -a /etc/hosts << EOF

# NGINX Ingress Controller entries for Personal Finance Tracker
$LB_IP finance-app.local
$LB_IP grafana.local
$LB_IP prometheus.local
EOF

# Verify the entries
tail -5 /etc/hosts
```

### Step 4: Test DNS Resolution

```bash
# Test DNS resolution
nslookup finance-app.local
nslookup grafana.local
nslookup prometheus.local

# Expected output for each:
# Server:    127.0.0.53
# Address:   127.0.0.53#53
# 
# Name:   finance-app.local
# Address: 52.12.34.56

# Test with ping (may not work due to AWS LB configuration)
ping -c 3 finance-app.local
```

### Step 5: Test HTTP Connectivity

```bash
# Test Finance App
curl -v -H "Host: finance-app.local" http://finance-app.local/

# Test with specific IP and Host header (alternative method)
curl -v -H "Host: finance-app.local" http://$LB_IP/

# Test Grafana
curl -v -H "Host: grafana.local" http://grafana.local/

# Test Prometheus
curl -v -H "Host: prometheus.local" http://prometheus.local/

# Test health endpoints
curl -H "Host: finance-app.local" http://finance-app.local/health
```

### Step 6: Browser Testing

1. **Open your browser**
2. **Navigate to**: `http://finance-app.local`
3. **You should see**: Your Personal Finance Tracker application
4. **Test other URLs**:
   - `http://grafana.local` (Grafana dashboard)
   - `http://prometheus.local` (Prometheus UI)

### Step 7: Advanced Testing with Different Paths

```bash
# Test different paths if using advanced routing
curl -H "Host: finance-app.local" http://finance-app.local/app/
curl -H "Host: finance-app.local" http://finance-app.local/api/
curl -H "Host: finance-app.local" http://finance-app.local/static/
curl -H "Host: finance-app.local" http://finance-app.local/metrics
curl -H "Host: finance-app.local" http://finance-app.local/grafana/
curl -H "Host: finance-app.local" http://finance-app.local/prometheus/
```

### Step 8: Test NGINX Ingress Controller Metrics

```bash
# Test NGINX metrics endpoint
curl http://$LB_IP:10254/metrics

# Or if metrics are exposed via ingress
kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller-metrics 10254:10254 &
curl http://localhost:10254/metrics
```

### Troubleshooting DNS Issues

#### Issue 1: DNS Not Resolving

```bash
# Check /etc/hosts syntax
cat /etc/hosts | grep -E "(finance-app|grafana|prometheus)"

# Ensure no extra spaces or characters
# Correct format: IP_ADDRESS HOSTNAME

# Test with explicit IP
curl -v -H "Host: finance-app.local" http://52.12.34.56/
```

#### Issue 2: Connection Refused

```bash
# Check if Load Balancer is ready
kubectl get svc -n ingress-nginx ingress-nginx-controller

# Check NGINX Ingress Controller logs
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller

# Check if Ingress resources are created
kubectl get ingress -A
```

#### Issue 3: 404 Not Found

```bash
# Check Ingress rules
kubectl describe ingress finance-tracker-ingress -n finance-tracker

# Check backend services
kubectl get svc -n finance-tracker finance-app-service
kubectl get endpoints -n finance-tracker finance-app-service

# Test backend service directly
kubectl port-forward -n finance-tracker svc/finance-app-service 8080:80 &
curl http://localhost:8080/
```

## Advanced Features

### 1. SSL/TLS Configuration with cert-manager

#### Install cert-manager

```bash
# Add cert-manager repository
helm repo add jetstack https://charts.jetstack.io
helm repo update

# Install cert-manager
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --version v1.13.0 \
  --set installCRDs=true
```

#### Create ClusterIssuer

**File: `/home/prameshwar/Desktop/k8s/letsencrypt-issuer.yaml`**
```yaml
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
---
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-staging
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com  # Replace with your email
    privateKeySecretRef:
      name: letsencrypt-staging
    solvers:
    - http01:
        ingress:
          class: nginx
```

#### Update Ingress for HTTPS

**File: `/home/prameshwar/Desktop/k8s/finance-tracker-ingress-https.yaml`**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: finance-tracker-ingress-https
  namespace: finance-tracker
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - finance-app.yourdomain.com  # Replace with your actual domain
    secretName: finance-app-tls
  rules:
  - host: finance-app.yourdomain.com
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

### 2. Authentication with oauth2-proxy

#### Install oauth2-proxy

```bash
# Add oauth2-proxy Helm repository
helm repo add oauth2-proxy https://oauth2-proxy.github.io/manifests
helm repo update

# Create values file for oauth2-proxy
cat > oauth2-proxy-values.yaml << EOF
config:
  clientID: "your-oauth-client-id"
  clientSecret: "your-oauth-client-secret"
  cookieSecret: "$(openssl rand -base64 32 | head -c 32 | base64)"
  
  # Configure for your OAuth provider (Google, GitHub, etc.)
  configFile: |-
    email_domains = [ "*" ]
    upstreams = [ "file:///dev/null" ]
    
ingress:
  enabled: true
  className: nginx
  hosts:
    - host: auth.finance-app.local
      paths:
        - path: /
          pathType: Prefix
EOF

# Install oauth2-proxy
helm install oauth2-proxy oauth2-proxy/oauth2-proxy \
  --namespace ingress-nginx \
  --values oauth2-proxy-values.yaml
```

#### Update Ingress with Authentication

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: finance-tracker-ingress-auth
  namespace: finance-tracker
  annotations:
    kubernetes.io/ingress.class: "nginx"
    nginx.ingress.kubernetes.io/auth-url: "https://auth.finance-app.local/oauth2/auth"
    nginx.ingress.kubernetes.io/auth-signin: "https://auth.finance-app.local/oauth2/start?rd=$escaped_request_uri"
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

### 3. Rate Limiting and DDoS Protection

**File: `/home/prameshwar/Desktop/k8s/rate-limiting-ingress.yaml`**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: finance-tracker-rate-limited
  namespace: finance-tracker
  annotations:
    kubernetes.io/ingress.class: "nginx"
    
    # Global rate limiting
    nginx.ingress.kubernetes.io/rate-limit: "100"  # requests per minute
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
    
    # Per-IP rate limiting
    nginx.ingress.kubernetes.io/rate-limit-rps: "10"  # requests per second per IP
    
    # Connection limiting
    nginx.ingress.kubernetes.io/limit-connections: "20"
    
    # Whitelist specific IPs (optional)
    nginx.ingress.kubernetes.io/whitelist-source-range: "10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"
    
    # Custom rate limiting configuration
    nginx.ingress.kubernetes.io/configuration-snippet: |
      # Rate limit for login endpoint
      location /login {
        limit_req zone=login burst=5 nodelay;
      }
      
      # Rate limit for API endpoints
      location /api {
        limit_req zone=api burst=20 nodelay;
      }
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

### 4. Custom Error Pages

**File: `/home/prameshwar/Desktop/k8s/custom-error-pages.yaml`**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: custom-error-pages
  namespace: ingress-nginx
data:
  404.html: |
    <!DOCTYPE html>
    <html>
    <head>
        <title>Page Not Found - Personal Finance Tracker</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }
            .error-code { font-size: 72px; color: #e74c3c; }
            .error-message { font-size: 24px; color: #34495e; }
        </style>
    </head>
    <body>
        <div class="error-code">404</div>
        <div class="error-message">Page Not Found</div>
        <p>The page you're looking for doesn't exist.</p>
        <a href="/">Return to Finance Tracker</a>
    </body>
    </html>
  
  503.html: |
    <!DOCTYPE html>
    <html>
    <head>
        <title>Service Unavailable - Personal Finance Tracker</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }
            .error-code { font-size: 72px; color: #f39c12; }
            .error-message { font-size: 24px; color: #34495e; }
        </style>
    </head>
    <body>
        <div class="error-code">503</div>
        <div class="error-message">Service Temporarily Unavailable</div>
        <p>We're performing maintenance. Please try again later.</p>
    </body>
    </html>
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: custom-error-pages
  namespace: ingress-nginx
spec:
  replicas: 1
  selector:
    matchLabels:
      app: custom-error-pages
  template:
    metadata:
      labels:
        app: custom-error-pages
    spec:
      containers:
      - name: error-pages
        image: nginx:alpine
        ports:
        - containerPort: 80
        volumeMounts:
        - name: error-pages
          mountPath: /usr/share/nginx/html
      volumes:
      - name: error-pages
        configMap:
          name: custom-error-pages
---
apiVersion: v1
kind: Service
metadata:
  name: custom-error-pages
  namespace: ingress-nginx
spec:
  selector:
    app: custom-error-pages
  ports:
  - port: 80
    targetPort: 80
```

### 5. Monitoring and Observability

#### NGINX Ingress Metrics

```bash
# Check if metrics are enabled
kubectl get svc -n ingress-nginx | grep metrics

# Port forward to access metrics
kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller-metrics 10254:10254 &

# View metrics
curl http://localhost:10254/metrics | grep nginx_ingress
```

#### Prometheus ServiceMonitor

**File: `/home/prameshwar/Desktop/k8s/nginx-ingress-servicemonitor.yaml`**
```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: nginx-ingress-controller
  namespace: monitoring
  labels:
    app.kubernetes.io/name: ingress-nginx
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: ingress-nginx
      app.kubernetes.io/component: controller
  namespaceSelector:
    matchNames:
    - ingress-nginx
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
```

#### Grafana Dashboard for NGINX Ingress

```bash
# Import NGINX Ingress Controller dashboard
# Dashboard ID: 9614
# Go to Grafana → "+" → Import → Enter ID: 9614
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Ingress Controller Not Starting

**Symptoms:**
```bash
kubectl get pods -n ingress-nginx
# NAME                                        READY   STATUS             RESTARTS   AGE
# ingress-nginx-controller-xxx-xxx            0/1     CrashLoopBackOff   3          2m
```

**Diagnosis:**
```bash
# Check logs
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller

# Check events
kubectl get events -n ingress-nginx --sort-by='.lastTimestamp'

# Check resource constraints
kubectl describe pod -n ingress-nginx <pod-name>
```

**Common Solutions:**
```bash
# Insufficient resources
kubectl patch deployment ingress-nginx-controller -n ingress-nginx -p '{"spec":{"template":{"spec":{"containers":[{"name":"controller","resources":{"requests":{"cpu":"50m","memory":"64Mi"}}}]}}}}'

# Port conflicts
kubectl get svc -A | grep -E ":80|:443"

# RBAC issues
kubectl auth can-i get ingresses --as=system:serviceaccount:ingress-nginx:ingress-nginx
```

#### 2. Load Balancer Not Getting External IP

**Symptoms:**
```bash
kubectl get svc -n ingress-nginx
# NAME                       TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)
# ingress-nginx-controller   LoadBalancer   10.100.x.x     <pending>     80:32080/TCP,443:32443/TCP
```

**Solutions:**
```bash
# Check AWS Load Balancer Controller
kubectl get pods -n kube-system | grep aws-load-balancer

# Check service annotations
kubectl describe svc -n ingress-nginx ingress-nginx-controller

# Check AWS permissions
aws elbv2 describe-load-balancers --region us-east-1

# Force recreation
kubectl delete svc -n ingress-nginx ingress-nginx-controller
helm upgrade ingress-nginx ingress-nginx/ingress-nginx -n ingress-nginx --values nginx-ingress-values.yaml
```

#### 3. 404 Not Found Errors

**Symptoms:**
- Browser shows 404 error
- `curl` returns 404

**Diagnosis:**
```bash
# Check Ingress resources
kubectl get ingress -A

# Check Ingress rules
kubectl describe ingress finance-tracker-ingress -n finance-tracker

# Check backend services
kubectl get svc -n finance-tracker
kubectl get endpoints -n finance-tracker
```

**Solutions:**
```bash
# Verify service names match
kubectl get svc -n finance-tracker finance-app-service

# Check service selector
kubectl describe svc -n finance-tracker finance-app-service

# Test backend directly
kubectl port-forward -n finance-tracker svc/finance-app-service 8080:80 &
curl http://localhost:8080/

# Check Ingress class
kubectl get ingressclass
```

#### 4. SSL/TLS Issues

**Symptoms:**
- Certificate errors in browser
- HTTPS not working

**Diagnosis:**
```bash
# Check TLS secrets
kubectl get secrets -n finance-tracker | grep tls

# Check certificate status
kubectl describe certificate finance-app-tls -n finance-tracker

# Check cert-manager logs
kubectl logs -n cert-manager deployment/cert-manager
```

**Solutions:**
```bash
# Delete and recreate certificate
kubectl delete certificate finance-app-tls -n finance-tracker
kubectl apply -f finance-tracker-ingress-https.yaml

# Check ClusterIssuer
kubectl describe clusterissuer letsencrypt-prod

# Manual certificate creation
kubectl create secret tls finance-app-tls \
  --cert=path/to/cert.pem \
  --key=path/to/key.pem \
  -n finance-tracker
```

#### 5. Performance Issues

**Symptoms:**
- Slow response times
- High CPU/memory usage

**Diagnosis:**
```bash
# Check resource usage
kubectl top pods -n ingress-nginx

# Check NGINX metrics
curl http://localhost:10254/metrics | grep -E "(request_duration|connections)"

# Check backend response times
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller | grep "upstream_response_time"
```

**Solutions:**
```bash
# Increase resources
helm upgrade ingress-nginx ingress-nginx/ingress-nginx \
  -n ingress-nginx \
  --set controller.resources.requests.cpu=200m \
  --set controller.resources.requests.memory=256Mi

# Tune NGINX configuration
kubectl patch configmap ingress-nginx-controller -n ingress-nginx --patch '{"data":{"worker-processes":"auto","worker-connections":"2048"}}'

# Scale replicas
kubectl scale deployment ingress-nginx-controller --replicas=3 -n ingress-nginx
```

### Health Check Commands

```bash
# Complete health check script
#!/bin/bash

echo "=== NGINX Ingress Controller Health Check ==="

# 1. Check pods
echo "1. Checking pods..."
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
    curl -s -o /dev/null -w "%{http_code}" -H "Host: finance-app.local" http://$LB_URL/
    echo " - Finance App"
    curl -s -o /dev/null -w "%{http_code}" -H "Host: grafana.local" http://$LB_URL/
    echo " - Grafana"
else
    echo "Load Balancer not ready"
fi

# 5. Check logs for errors
echo "5. Checking recent logs for errors..."
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller --tail=10 | grep -i error

echo "=== Health Check Complete ==="
```
## Interview Questions

### Basic Level Questions

#### 1. What is an Ingress Controller and how does it differ from a regular Load Balancer?

**Answer:**
An Ingress Controller is a Kubernetes-native load balancer that operates at Layer 7 (HTTP/HTTPS) and provides advanced routing capabilities. Key differences:

**Ingress Controller:**
- Layer 7 (HTTP/HTTPS) routing
- Path-based and host-based routing
- SSL termination
- Single entry point for multiple services
- Kubernetes-native configuration
- Advanced features (rate limiting, auth, caching)

**Regular Load Balancer:**
- Layer 4 (TCP/UDP) or basic Layer 7
- Simple port-based routing
- One load balancer per service
- Cloud provider managed
- Limited routing capabilities

#### 2. Explain the difference between NGINX Ingress Controller and AWS Application Load Balancer (ALB).

**Answer:**
| Feature | NGINX Ingress | AWS ALB |
|---------|---------------|---------|
| **Cost** | Single LB for all services | One ALB per service |
| **Routing** | Advanced regex, rewrite rules | Basic path/host routing |
| **Features** | Rate limiting, auth, caching | Basic features, needs WAF |
| **SSL** | cert-manager integration | AWS Certificate Manager |
| **Configuration** | Kubernetes annotations | AWS console/CLI |
| **Vendor Lock-in** | Portable across clouds | AWS-specific |

#### 3. What are the main components of NGINX Ingress Controller?

**Answer:**
1. **Ingress Controller Pod**: Runs NGINX with Kubernetes integration
2. **Ingress Resources**: Define routing rules (host, path, backend)
3. **ConfigMap**: Global NGINX configuration
4. **Service**: Exposes controller to external load balancer
5. **RBAC**: Permissions to read Ingress resources and services
6. **Default Backend**: Handles requests that don't match any rules

#### 4. How does NGINX Ingress Controller discover backend services?

**Answer:**
1. **Watches Kubernetes API**: Monitors Ingress resources, Services, and Endpoints
2. **Service Discovery**: Automatically discovers services referenced in Ingress rules
3. **Endpoint Updates**: Updates backend pool when pods are added/removed
4. **Configuration Reload**: Dynamically updates NGINX configuration without restart
5. **Health Checks**: Monitors backend pod health and removes unhealthy endpoints

### Intermediate Level Questions

#### 5. Explain the request flow through NGINX Ingress Controller.

**Answer:**
```
1. Client Request → DNS Resolution → Load Balancer IP
2. Load Balancer → Routes to NGINX Ingress Controller Pod
3. NGINX Controller → Reads Host header and URL path
4. Rule Matching → Finds matching Ingress rule
5. SSL Termination → Decrypts HTTPS (if applicable)
6. Request Processing → Applies annotations (auth, rate limiting, etc.)
7. Backend Selection → Routes to appropriate Kubernetes service
8. Service → Load balances to healthy backend pods
9. Response → Flows back through the same path
```

#### 6. How would you implement SSL/TLS termination with NGINX Ingress?

**Answer:**
```yaml
# 1. Install cert-manager
helm install cert-manager jetstack/cert-manager --set installCRDs=true

# 2. Create ClusterIssuer
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx

# 3. Update Ingress with TLS
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - myapp.example.com
    secretName: myapp-tls
  rules:
  - host: myapp.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: myapp-service
            port:
              number: 80
```

#### 7. How do you implement rate limiting in NGINX Ingress?

**Answer:**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  annotations:
    # Global rate limiting
    nginx.ingress.kubernetes.io/rate-limit: "100"  # requests per minute
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
    
    # Per-IP rate limiting
    nginx.ingress.kubernetes.io/rate-limit-rps: "10"  # requests per second per IP
    
    # Connection limiting
    nginx.ingress.kubernetes.io/limit-connections: "20"
    
    # Custom rate limiting for specific paths
    nginx.ingress.kubernetes.io/configuration-snippet: |
      location /api/login {
        limit_req zone=login burst=5 nodelay;
      }
      location /api {
        limit_req zone=api burst=20 nodelay;
      }
```

#### 8. What are the different types of path matching in Ingress?

**Answer:**
1. **Exact**: Matches the exact path
   ```yaml
   path: /api/v1/users
   pathType: Exact
   ```

2. **Prefix**: Matches path prefix
   ```yaml
   path: /api
   pathType: Prefix  # Matches /api, /api/, /api/v1, etc.
   ```

3. **ImplementationSpecific**: Depends on Ingress Controller
   ```yaml
   path: /api/.*
   pathType: ImplementationSpecific  # NGINX supports regex
   ```

### Advanced Level Questions

#### 9. How would you implement Blue-Green deployment using NGINX Ingress?

**Answer:**
```yaml
# Blue-Green with weighted traffic splitting
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  annotations:
    nginx.ingress.kubernetes.io/canary: "true"
    nginx.ingress.kubernetes.io/canary-weight: "10"  # 10% to green
spec:
  rules:
  - host: myapp.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: myapp-green-service  # New version
            port:
              number: 80
---
# Main ingress (90% traffic to blue)
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp-blue
spec:
  rules:
  - host: myapp.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: myapp-blue-service  # Current version
            port:
              number: 80
```

#### 10. How do you troubleshoot NGINX Ingress Controller issues?

**Answer:**
```bash
# 1. Check controller status
kubectl get pods -n ingress-nginx
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller

# 2. Verify Ingress resources
kubectl get ingress -A
kubectl describe ingress myapp-ingress -n myapp

# 3. Check backend services
kubectl get svc -n myapp
kubectl get endpoints -n myapp

# 4. Test connectivity
kubectl port-forward -n myapp svc/myapp-service 8080:80
curl http://localhost:8080/

# 5. Check NGINX configuration
kubectl exec -n ingress-nginx deployment/ingress-nginx-controller -- cat /etc/nginx/nginx.conf

# 6. Monitor metrics
curl http://controller-ip:10254/metrics

# 7. Check events
kubectl get events -n ingress-nginx --sort-by='.lastTimestamp'
```

#### 11. Explain how to implement authentication with NGINX Ingress.

**Answer:**
```yaml
# Method 1: Basic Authentication
# Create htpasswd secret
htpasswd -c auth admin
kubectl create secret generic basic-auth --from-file=auth

apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  annotations:
    nginx.ingress.kubernetes.io/auth-type: basic
    nginx.ingress.kubernetes.io/auth-secret: basic-auth
    nginx.ingress.kubernetes.io/auth-realm: 'Authentication Required'

# Method 2: OAuth2 Proxy
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  annotations:
    nginx.ingress.kubernetes.io/auth-url: "https://oauth2-proxy.example.com/oauth2/auth"
    nginx.ingress.kubernetes.io/auth-signin: "https://oauth2-proxy.example.com/oauth2/start?rd=$escaped_request_uri"

# Method 3: External Auth Service
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  annotations:
    nginx.ingress.kubernetes.io/auth-url: "http://auth-service.auth.svc.cluster.local/auth"
    nginx.ingress.kubernetes.io/auth-method: "GET"
    nginx.ingress.kubernetes.io/auth-response-headers: "X-User,X-Email"
```

#### 12. How do you implement custom error pages in NGINX Ingress?

**Answer:**
```yaml
# 1. Create ConfigMap with error pages
apiVersion: v1
kind: ConfigMap
metadata:
  name: custom-error-pages
  namespace: ingress-nginx
data:
  404.html: |
    <html><body><h1>Custom 404 Page</h1></body></html>
  503.html: |
    <html><body><h1>Service Unavailable</h1></body></html>

# 2. Create deployment to serve error pages
apiVersion: apps/v1
kind: Deployment
metadata:
  name: custom-error-pages
  namespace: ingress-nginx
spec:
  replicas: 1
  selector:
    matchLabels:
      app: custom-error-pages
  template:
    metadata:
      labels:
        app: custom-error-pages
    spec:
      containers:
      - name: error-pages
        image: nginx:alpine
        volumeMounts:
        - name: error-pages
          mountPath: /usr/share/nginx/html
      volumes:
      - name: error-pages
        configMap:
          name: custom-error-pages

# 3. Create service
apiVersion: v1
kind: Service
metadata:
  name: custom-error-pages
  namespace: ingress-nginx
spec:
  selector:
    app: custom-error-pages
  ports:
  - port: 80

# 4. Configure Ingress to use custom error pages
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  annotations:
    nginx.ingress.kubernetes.io/custom-http-errors: "404,503"
    nginx.ingress.kubernetes.io/default-backend: "custom-error-pages"
```

### Scenario-Based Questions

#### 13. You have a microservices application with 10 services. How would you design the Ingress architecture?

**Answer:**
```yaml
# Option 1: Single Ingress with path-based routing
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: microservices-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /$2
spec:
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /user(/|$)(.*)
        pathType: Prefix
        backend:
          service:
            name: user-service
            port:
              number: 80
      - path: /order(/|$)(.*)
        pathType: Prefix
        backend:
          service:
            name: order-service
            port:
              number: 80
      - path: /payment(/|$)(.*)
        pathType: Prefix
        backend:
          service:
            name: payment-service
            port:
              number: 80

# Option 2: Multiple Ingresses with subdomain routing
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: user-service-ingress
spec:
  rules:
  - host: user.api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: user-service
            port:
              number: 80
```

#### 14. How would you handle a situation where your NGINX Ingress Controller is consuming too much memory?

**Answer:**
```bash
# 1. Identify the issue
kubectl top pods -n ingress-nginx
kubectl describe pod -n ingress-nginx <controller-pod>

# 2. Check NGINX configuration
kubectl exec -n ingress-nginx deployment/ingress-nginx-controller -- nginx -T

# 3. Optimize configuration
kubectl patch configmap ingress-nginx-controller -n ingress-nginx --patch '
{
  "data": {
    "worker-processes": "auto",
    "worker-connections": "1024",
    "worker-rlimit-nofile": "65535",
    "keepalive-requests": "100",
    "client-body-buffer-size": "8k",
    "client-header-buffer-size": "1k"
  }
}'

# 4. Increase resource limits
helm upgrade ingress-nginx ingress-nginx/ingress-nginx \
  -n ingress-nginx \
  --set controller.resources.limits.memory=1Gi \
  --set controller.resources.requests.memory=512Mi

# 5. Scale horizontally
kubectl scale deployment ingress-nginx-controller --replicas=3 -n ingress-nginx
```

#### 15. Explain how you would implement A/B testing using NGINX Ingress.

**Answer:**
```yaml
# A/B Testing with header-based routing
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-version-b
  annotations:
    nginx.ingress.kubernetes.io/canary: "true"
    nginx.ingress.kubernetes.io/canary-by-header: "X-Version"
    nginx.ingress.kubernetes.io/canary-by-header-value: "beta"
spec:
  rules:
  - host: myapp.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app-service-v2
            port:
              number: 80
---
# A/B Testing with cookie-based routing
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-version-b-cookie
  annotations:
    nginx.ingress.kubernetes.io/canary: "true"
    nginx.ingress.kubernetes.io/canary-by-cookie: "version"
    nginx.ingress.kubernetes.io/canary-by-cookie-value: "beta"
---
# A/B Testing with percentage-based routing
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-version-b-weight
  annotations:
    nginx.ingress.kubernetes.io/canary: "true"
    nginx.ingress.kubernetes.io/canary-weight: "20"  # 20% traffic to version B
```

### Performance and Scaling Questions

#### 16. How do you optimize NGINX Ingress Controller for high traffic?

**Answer:**
```yaml
# 1. Optimize NGINX configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: ingress-nginx-controller
  namespace: ingress-nginx
data:
  worker-processes: "auto"
  worker-connections: "4096"
  worker-rlimit-nofile: "65535"
  keepalive-requests: "1000"
  keepalive-timeout: "65"
  client-body-buffer-size: "16k"
  client-header-buffer-size: "4k"
  large-client-header-buffers: "8 16k"
  proxy-buffer-size: "8k"
  proxy-buffers: "8 8k"
  proxy-busy-buffers-size: "16k"
  
# 2. Scale controller replicas
kubectl scale deployment ingress-nginx-controller --replicas=5 -n ingress-nginx

# 3. Use pod anti-affinity
spec:
  affinity:
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchExpressions:
          - key: app.kubernetes.io/name
            operator: In
            values:
            - ingress-nginx
        topologyKey: kubernetes.io/hostname

# 4. Increase resource limits
resources:
  requests:
    cpu: 500m
    memory: 1Gi
  limits:
    cpu: 2000m
    memory: 2Gi
```

#### 17. What monitoring and alerting would you set up for NGINX Ingress?

**Answer:**
```yaml
# 1. Enable metrics
controller:
  metrics:
    enabled: true
    serviceMonitor:
      enabled: true

# 2. Key metrics to monitor
# - nginx_ingress_controller_requests (request rate)
# - nginx_ingress_controller_request_duration_seconds (latency)
# - nginx_ingress_controller_response_size (response size)
# - nginx_ingress_controller_ssl_expire_time_seconds (SSL expiry)

# 3. Prometheus alerts
groups:
- name: nginx-ingress
  rules:
  - alert: NginxIngressControllerDown
    expr: up{job="ingress-nginx-controller-metrics"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "NGINX Ingress Controller is down"
  
  - alert: NginxIngressHighLatency
    expr: histogram_quantile(0.95, sum(rate(nginx_ingress_controller_request_duration_seconds_bucket[5m])) by (le)) > 1
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High latency in NGINX Ingress"
  
  - alert: NginxIngressHighErrorRate
    expr: sum(rate(nginx_ingress_controller_requests{status=~"5.."}[5m])) / sum(rate(nginx_ingress_controller_requests[5m])) > 0.05
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "High error rate in NGINX Ingress"
```

These interview questions cover the full spectrum from basic concepts to advanced implementation scenarios, helping you prepare for roles involving NGINX Ingress Controller in Kubernetes environments.
