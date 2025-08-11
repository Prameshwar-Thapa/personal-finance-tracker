# Personal Finance Tracker - Minikube Deployment Guide

This comprehensive guide walks you through deploying the Personal Finance Tracker application on Minikube using Kubernetes best practices, including StatefulSets for PostgreSQL and NodePort services for testing.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Minikube Setup](#minikube-setup)
3. [Kubernetes Manifests Overview](#kubernetes-manifests-overview)
4. [StatefulSet Concepts for PostgreSQL](#statefulset-concepts-for-postgresql)
5. [Step-by-Step Deployment](#step-by-step-deployment)
6. [Testing with NodePort](#testing-with-nodeport)
7. [Troubleshooting](#troubleshooting)
8. [Cleanup](#cleanup)

## 🔧 Prerequisites

Before starting, ensure you have the following installed:

```bash
# Check if tools are installed
minikube version
kubectl version --client
docker version
```

### Required Tools:
- **Minikube**: Local Kubernetes cluster
- **kubectl**: Kubernetes command-line tool
- **Docker**: Container runtime
- **VirtualBox/Docker Desktop**: Virtualization (depending on your setup)

### Installation Commands:

```bash
# Install Minikube (Linux)
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Install kubectl (Linux)
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Verify installations
minikube version
kubectl version --client
```

## 🚀 Minikube Setup

### 1. Start Minikube Cluster

```bash
# Start minikube with sufficient resources
minikube start --driver=docker --memory=4096 --cpus=2 --disk-size=20g

# Verify cluster is running
minikube status
kubectl cluster-info
```

### 2. Enable Required Addons

```bash
# Enable ingress addon (optional, for future use)
minikube addons enable ingress

# Enable metrics server for resource monitoring
minikube addons enable metrics-server

# List all enabled addons
minikube addons list
```

### 3. Configure Docker Environment

```bash
# Configure shell to use minikube's Docker daemon
eval $(minikube docker-env)

# Verify Docker context
docker ps
```

## 📁 Kubernetes Manifests Overview

We'll create the following Kubernetes resources:

1. **Namespace**: Isolate our application resources
2. **ConfigMap**: Store non-sensitive configuration
3. **Secret**: Store sensitive data (database credentials)
4. **PersistentVolume & PersistentVolumeClaim**: Storage for PostgreSQL
5. **StatefulSet**: PostgreSQL database with persistent storage
6. **Deployment**: Flask web application
7. **Services**: Expose applications (NodePort for testing)

## 🗄️ StatefulSet Concepts for PostgreSQL

### Why StatefulSet for PostgreSQL?

**StatefulSets** are designed for stateful applications that require:

- **Stable Network Identity**: Each pod gets a predictable hostname
- **Persistent Storage**: Data survives pod restarts and rescheduling
- **Ordered Deployment**: Pods are created/deleted in a specific order
- **Stable Storage**: Each pod gets its own persistent volume

### StatefulSet vs Deployment

| Feature | StatefulSet | Deployment |
|---------|-------------|------------|
| Pod Names | Predictable (postgres-0, postgres-1) | Random |
| Storage | Persistent per pod | Shared or ephemeral |
| Scaling | Ordered (0→1→2) | Parallel |
| Use Case | Databases, queues | Stateless apps |

### PostgreSQL StatefulSet Benefits

1. **Data Persistence**: Database survives pod crashes
2. **Consistent Identity**: Always connects to the same storage
3. **Ordered Operations**: Ensures proper database initialization
4. **Volume Management**: Automatic PVC creation and binding

## 📝 Step-by-Step Deployment

### Step 1: Create Kubernetes Manifests Directory

```bash
# Create k8s directory in your project
mkdir -p k8s
cd k8s
```

### Step 2: Create Namespace

```bash
# Create namespace.yaml
cat > namespace.yaml << 'EOF'
apiVersion: v1
kind: Namespace
metadata:
  name: finance-app
  labels:
    name: finance-app
    app: personal-finance-tracker
EOF
```

### Step 3: Create ConfigMap

```bash
# Create configmap.yaml
cat > configmap.yaml << 'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: finance-app-config
  namespace: finance-app
data:
  FLASK_ENV: "production"
  UPLOAD_FOLDER: "/app/static/uploads/receipts"
  MAX_CONTENT_LENGTH: "16777216"  # 16MB
  POSTGRES_DB: "financedb"
  POSTGRES_USER: "financeuser"
  REDIS_URL: "redis://redis-service:6379/0"
EOF
```

### Step 4: Create Secrets

```bash
# Create secrets.yaml
cat > secrets.yaml << 'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: finance-app-secrets
  namespace: finance-app
type: Opaque
data:
  # Base64 encoded values
  # postgres-password = "financepass123"
  postgres-password: ZmluYW5jZXBhc3MxMjM=
  # secret-key = "your-super-secret-key-change-in-production"
  secret-key: eW91ci1zdXBlci1zZWNyZXQta2V5LWNoYW5nZS1pbi1wcm9kdWN0aW9u
  # database-url = "postgresql://financeuser:financepass123@postgres-service:5432/financedb"
  database-url: cG9zdGdyZXNxbDovL2ZpbmFuY2V1c2VyOmZpbmFuY2VwYXNzMTIzQHBvc3RncmVzLXNlcnZpY2U6NTQzMi9maW5hbmNlZGI=
EOF
```

### Step 5: Create Persistent Volume

```bash
# Create persistent-volume.yaml
cat > persistent-volume.yaml << 'EOF'
apiVersion: v1
kind: PersistentVolume
metadata:
  name: postgres-pv
  labels:
    app: postgres
spec:
  capacity:
    storage: 5Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: standard
  hostPath:
    path: /data/postgres
    type: DirectoryOrCreate
---
apiVersion: v1
kind: PersistentVolume
metadata:
  name: uploads-pv
  labels:
    app: finance-app
spec:
  capacity:
    storage: 2Gi
  accessModes:
    - ReadWriteMany
  persistentVolumeReclaimPolicy: Retain
  storageClassName: standard
  hostPath:
    path: /data/uploads
    type: DirectoryOrCreate
EOF
```

### Step 6: Create PostgreSQL StatefulSet

```bash
# Create postgres-statefulset.yaml
cat > postgres-statefulset.yaml << 'EOF'
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: finance-app
  labels:
    app: postgres
spec:
  ports:
  - port: 5432
    name: postgres
  clusterIP: None  # Headless service for StatefulSet
  selector:
    app: postgres
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: finance-app
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
        ports:
        - containerPort: 5432
          name: postgres
        env:
        - name: POSTGRES_DB
          valueFrom:
            configMapKeyRef:
              name: finance-app-config
              key: POSTGRES_DB
        - name: POSTGRES_USER
          valueFrom:
            configMapKeyRef:
              name: finance-app-config
              key: POSTGRES_USER
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: finance-app-secrets
              key: postgres-password
        - name: PGDATA
          value: /var/lib/postgresql/data/pgdata
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        livenessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - $(POSTGRES_USER)
            - -d
            - $(POSTGRES_DB)
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - $(POSTGRES_USER)
            - -d
            - $(POSTGRES_DB)
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: standard
      resources:
        requests:
          storage: 5Gi
EOF
```

### Step 7: Create Redis Deployment

```bash
# Create redis-deployment.yaml
cat > redis-deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: finance-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        livenessProbe:
          exec:
            command:
            - redis-cli
            - ping
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - redis-cli
            - ping
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
---
apiVersion: v1
kind: Service
metadata:
  name: redis-service
  namespace: finance-app
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
EOF
```

### Step 8: Build Application Image

```bash
# Navigate back to project root
cd ..

# Build Docker image in minikube's Docker environment
eval $(minikube docker-env)
docker build -t finance-tracker:latest .

# Verify image is built
docker images | grep finance-tracker
```

### Step 9: Create Application Deployment

```bash
# Create k8s/app-deployment.yaml
cat > k8s/app-deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: finance-app
  namespace: finance-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: finance-app
  template:
    metadata:
      labels:
        app: finance-app
    spec:
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
              key: postgres-password
      containers:
      - name: finance-app
        image: finance-tracker:latest
        imagePullPolicy: Never  # Use local image
        ports:
        - containerPort: 5000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: finance-app-secrets
              key: database-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: finance-app-secrets
              key: secret-key
        - name: FLASK_ENV
          valueFrom:
            configMapKeyRef:
              name: finance-app-config
              key: FLASK_ENV
        - name: UPLOAD_FOLDER
          valueFrom:
            configMapKeyRef:
              name: finance-app-config
              key: UPLOAD_FOLDER
        volumeMounts:
        - name: uploads-storage
          mountPath: /app/static/uploads
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: uploads-storage
        persistentVolumeClaim:
          claimName: uploads-pvc
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: uploads-pvc
  namespace: finance-app
spec:
  accessModes:
    - ReadWriteMany
  storageClassName: standard
  resources:
    requests:
      storage: 2Gi
EOF
```

### Step 10: Create NodePort Service

```bash
# Create k8s/nodeport-service.yaml
cat > k8s/nodeport-service.yaml << 'EOF'
apiVersion: v1
kind: Service
metadata:
  name: finance-app-nodeport
  namespace: finance-app
  labels:
    app: finance-app
spec:
  type: NodePort
  selector:
    app: finance-app
  ports:
  - port: 80
    targetPort: 5000
    nodePort: 30080  # Accessible on minikube-ip:30080
    protocol: TCP
    name: http
---
apiVersion: v1
kind: Service
metadata:
  name: postgres-nodeport
  namespace: finance-app
  labels:
    app: postgres
spec:
  type: NodePort
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
    nodePort: 30432  # Accessible on minikube-ip:30432 for debugging
    protocol: TCP
    name: postgres
EOF
```

### Step 11: Deploy All Resources

```bash
# Apply all manifests in order
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/persistent-volume.yaml

# Wait a moment for PVs to be available
sleep 5

# Deploy PostgreSQL StatefulSet
kubectl apply -f k8s/postgres-statefulset.yaml

# Deploy Redis
kubectl apply -f k8s/redis-deployment.yaml

# Wait for database to be ready
echo "Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n finance-app --timeout=300s

# Deploy application
kubectl apply -f k8s/app-deployment.yaml

# Deploy NodePort services
kubectl apply -f k8s/nodeport-service.yaml
```

### Step 12: Verify Deployment

```bash
# Check all resources
kubectl get all -n finance-app

# Check persistent volumes
kubectl get pv
kubectl get pvc -n finance-app

# Check pod logs
kubectl logs -f deployment/finance-app -n finance-app

# Check StatefulSet status
kubectl get statefulset -n finance-app
kubectl describe statefulset postgres -n finance-app
```

## 🧪 Testing with NodePort

### 1. Get Minikube IP and Service URLs

```bash
# Get minikube IP
minikube ip

# Get service URLs
minikube service finance-app-nodeport -n finance-app --url

# Alternative: Manual URL construction
echo "Application URL: http://$(minikube ip):30080"
echo "PostgreSQL URL: $(minikube ip):30432"
```

### 2. Test Application Access

```bash
# Test health endpoint
curl http://$(minikube ip):30080/health

# Test main page
curl -I http://$(minikube ip):30080/

# Open in browser
minikube service finance-app-nodeport -n finance-app
```

### 3. Test Database Connection

```bash
# Connect to PostgreSQL from outside cluster
psql -h $(minikube ip) -p 30432 -U financeuser -d financedb

# Or test connection
pg_isready -h $(minikube ip) -p 30432 -U financeuser
```

### 4. Test Application Functionality

```bash
# Register a new user (using curl)
curl -X POST http://$(minikube ip):30080/register \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&email=test@example.com&password=testpass123"

# Login
curl -X POST http://$(minikube ip):30080/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass123" \
  -c cookies.txt

# Add a transaction
curl -X POST http://$(minikube ip):30080/add_transaction \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -b cookies.txt \
  -d "amount=25.50&description=Test Transaction&transaction_type=expense&category=Food"
```

### 5. Monitor Resources

```bash
# Watch pods
kubectl get pods -n finance-app -w

# Check resource usage
kubectl top pods -n finance-app
kubectl top nodes

# View detailed pod information
kubectl describe pod postgres-0 -n finance-app
kubectl describe deployment finance-app -n finance-app
```

## 🔍 Understanding StatefulSet Behavior

### StatefulSet Characteristics in Action

```bash
# Observe ordered pod creation
kubectl get pods -n finance-app -w

# Check persistent volume claims
kubectl get pvc -n finance-app

# Verify stable network identity
kubectl exec -it postgres-0 -n finance-app -- hostname
kubectl exec -it postgres-0 -n finance-app -- nslookup postgres-0.postgres-service.finance-app.svc.cluster.local
```

### StatefulSet Scaling (Optional)

```bash
# Scale PostgreSQL (not recommended for production)
kubectl scale statefulset postgres --replicas=2 -n finance-app

# Observe ordered scaling
kubectl get pods -n finance-app -w

# Scale back down
kubectl scale statefulset postgres --replicas=1 -n finance-app
```

### Data Persistence Verification

```bash
# Create test data
kubectl exec -it postgres-0 -n finance-app -- psql -U financeuser -d financedb -c "CREATE TABLE test_persistence (id SERIAL, data TEXT);"
kubectl exec -it postgres-0 -n finance-app -- psql -U financeuser -d financedb -c "INSERT INTO test_persistence (data) VALUES ('This data should persist');"

# Delete pod to test persistence
kubectl delete pod postgres-0 -n finance-app

# Wait for pod to restart
kubectl wait --for=condition=ready pod postgres-0 -n finance-app --timeout=300s

# Verify data persisted
kubectl exec -it postgres-0 -n finance-app -- psql -U financeuser -d financedb -c "SELECT * FROM test_persistence;"
```

## 🐛 Troubleshooting

### Common Issues and Solutions

#### 1. Pods Stuck in Pending State

```bash
# Check events
kubectl describe pod <pod-name> -n finance-app

# Check node resources
kubectl describe nodes

# Check PVC status
kubectl get pvc -n finance-app
kubectl describe pvc <pvc-name> -n finance-app
```

#### 2. Database Connection Issues

```bash
# Check PostgreSQL logs
kubectl logs postgres-0 -n finance-app

# Test database connectivity
kubectl exec -it postgres-0 -n finance-app -- pg_isready -U financeuser

# Check service endpoints
kubectl get endpoints -n finance-app
```

#### 3. Application Not Starting

```bash
# Check application logs
kubectl logs deployment/finance-app -n finance-app

# Check init container logs
kubectl logs <pod-name> -c wait-for-postgres -n finance-app

# Verify secrets and configmaps
kubectl get secrets -n finance-app
kubectl get configmaps -n finance-app
```

#### 4. NodePort Not Accessible

```bash
# Check service status
kubectl get svc -n finance-app

# Verify minikube tunnel (if needed)
minikube tunnel

# Check firewall rules
sudo ufw status
```

#### 5. Storage Issues

```bash
# Check persistent volumes
kubectl get pv
kubectl describe pv postgres-pv

# Check storage class
kubectl get storageclass

# Verify host paths (in minikube)
minikube ssh
ls -la /data/
```

### Debug Commands

```bash
# Get comprehensive cluster info
kubectl cluster-info dump

# Check all events
kubectl get events -n finance-app --sort-by='.lastTimestamp'

# Resource usage
kubectl top pods -n finance-app
kubectl top nodes

# Network debugging
kubectl exec -it <pod-name> -n finance-app -- nslookup postgres-service
kubectl exec -it <pod-name> -n finance-app -- ping postgres-service
```

## 🧹 Cleanup

### Complete Cleanup

```bash
# Delete all resources in namespace
kubectl delete namespace finance-app

# Delete persistent volumes (if needed)
kubectl delete pv postgres-pv uploads-pv

# Clean up minikube host paths
minikube ssh
sudo rm -rf /data/postgres /data/uploads
exit

# Stop minikube (optional)
minikube stop

# Delete minikube cluster (optional)
minikube delete
```

### Partial Cleanup (Keep Data)

```bash
# Delete only application components
kubectl delete deployment finance-app -n finance-app
kubectl delete deployment redis -n finance-app

# Keep StatefulSet and data
# kubectl delete statefulset postgres -n finance-app  # Don't run this to keep data
```

## 📊 Monitoring and Maintenance

### Regular Monitoring Commands

```bash
# Check cluster health
kubectl get componentstatuses

# Monitor resource usage
watch kubectl top pods -n finance-app

# Check persistent volume usage
kubectl exec -it postgres-0 -n finance-app -- df -h

# View application metrics
kubectl exec -it <app-pod> -n finance-app -- ps aux
```

### Backup Strategies

```bash
# Database backup
kubectl exec -it postgres-0 -n finance-app -- pg_dump -U financeuser financedb > backup.sql

# Upload files backup
kubectl exec -it <app-pod> -n finance-app -- tar -czf /tmp/uploads-backup.tar.gz /app/static/uploads
kubectl cp <app-pod>:/tmp/uploads-backup.tar.gz ./uploads-backup.tar.gz -n finance-app
```

## 🎯 Key Learning Points

### StatefulSet Benefits Demonstrated

1. **Persistent Identity**: `postgres-0` always connects to the same storage
2. **Ordered Operations**: Database initializes before application starts
3. **Data Persistence**: Data survives pod restarts and node failures
4. **Stable Network**: Predictable DNS names for service discovery

### Kubernetes Concepts Covered

- **Namespaces**: Resource isolation
- **ConfigMaps & Secrets**: Configuration management
- **StatefulSets**: Stateful application management
- **Persistent Volumes**: Storage abstraction
- **Services**: Network abstraction and load balancing
- **NodePort**: External access for testing
- **Health Checks**: Application monitoring
- **Init Containers**: Dependency management

### Production Considerations

- Use **Ingress** instead of NodePort for production
- Implement **TLS/SSL** certificates
- Add **resource quotas** and **limits**
- Set up **monitoring** with Prometheus/Grafana
- Implement **backup strategies**
- Use **Helm charts** for complex deployments
- Consider **database clustering** for high availability

---

## 🎉 Conclusion

You now have a fully functional Personal Finance Tracker running on Minikube with:

- ✅ PostgreSQL StatefulSet with persistent storage
- ✅ Redis caching layer
- ✅ Flask application with multiple replicas
- ✅ NodePort services for testing
- ✅ Proper health checks and monitoring
- ✅ Data persistence across pod restarts

The application is accessible at `http://<minikube-ip>:30080` and demonstrates production-ready Kubernetes deployment patterns with proper StatefulSet usage for database workloads.

**Next Steps:**
- Explore Ingress controllers for production routing
- Implement Helm charts for easier deployment management
- Add monitoring with Prometheus and Grafana
- Set up CI/CD pipelines for automated deployments
