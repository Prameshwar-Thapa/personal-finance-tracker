# Observability Guide: Prometheus & Grafana for Personal Finance Tracker (Helm Installation)

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Helm Installation Setup](#helm-installation-setup)
5. [Prometheus Installation with Helm](#prometheus-installation-with-helm)
6. [Grafana Installation with Helm](#grafana-installation-with-helm)
7. [Understanding Pods and Services](#understanding-pods-and-services)
8. [Testing & Verification](#testing--verification)
9. [Metrics Testing Guide](#metrics-testing-guide)
10. [Query Examples](#query-examples)
11. [Dashboards](#dashboards)
12. [Troubleshooting](#troubleshooting)

## Overview

This guide will help you set up a complete monitoring stack for your Personal Finance Tracker application running on EKS using **Helm Charts**:

- **Prometheus**: Metrics collection and storage (using kube-prometheus-stack)
- **Grafana**: Visualization and dashboards (included in kube-prometheus-stack)
- **Node Exporter**: System metrics (auto-included)
- **kube-state-metrics**: Kubernetes cluster metrics (auto-included)
- **Alertmanager**: Alert management (auto-included)

### What You'll Monitor
- Application performance (response times, error rates)
- Kubernetes cluster health (pods, nodes, resources)
- System metrics (CPU, memory, disk, network)
- Custom business metrics from your finance app

### Why Use Helm Charts?
- **Simplified Installation**: One command installs entire monitoring stack
- **Production Ready**: Pre-configured with best practices
- **Easy Updates**: Simple helm upgrade commands
- **Comprehensive**: Includes Prometheus, Grafana, AlertManager, and exporters
- **Customizable**: Easy to override default configurations

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Grafana       │    │   Prometheus    │    │  Your Finance   │
│   (Dashboard)   │◄───┤   (Metrics DB)  │◄───┤  App + Metrics  │
│   Port: 3000    │    │   Port: 9090    │    │   Port: 5000    │
│   NodePort:30030│    │   NodePort:30090│    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   NodePort      │    │   NodePort      │    │  ClusterIP      │
│   (External)    │    │   (External)    │    │  (Internal)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Additional Components                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ AlertManager│  │Node Exporter│  │kube-state   │             │
│  │Port: 9093   │  │Port: 9100   │  │metrics      │             │
│  └─────────────┘  └─────────────┘  │Port: 8080   │             │
│                                    └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

```bash
# Ensure you have kubectl access to your EKS cluster
kubectl get nodes

# Install Helm if not already installed
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Verify Helm installation
helm version

# Create monitoring namespace
kubectl create namespace monitoring
```

## Helm Installation Setup

### Step 1: Add Helm Repositories

```bash
# Add Prometheus community Helm repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts

# Add Grafana Helm repository (backup, as kube-prometheus-stack includes Grafana)
helm repo add grafana https://grafana.github.io/helm-charts

# Update repositories
helm repo update

# List available charts
helm search repo prometheus-community
```

## Prometheus Installation with Helm

### Step 1: Create Custom Values File

Create a custom values file to configure NodePort and other settings:

**File: `/home/prameshwar/Desktop/k8s/prometheus-values.yaml`**
```yaml
# Prometheus configuration
prometheus:
  prometheusSpec:
    # Storage configuration
    retention: 15d
    retentionSize: "10GB"
    
    # Resource limits
    resources:
      requests:
        memory: "1Gi"
        cpu: "500m"
      limits:
        memory: "2Gi"
        cpu: "1000m"
    
    # Storage class for persistent volume
    storageSpec:
      volumeClaimTemplate:
        spec:
          storageClassName: gp2  # AWS EBS storage class
          accessModes: ["ReadWriteOnce"]
          resources:
            requests:
              storage: 20Gi
    
    # Additional scrape configs for your finance app
    additionalScrapeConfigs:
      - job_name: 'finance-app'
        static_configs:
          - targets: ['finance-app-service.finance-tracker.svc.cluster.local:80']
        metrics_path: '/metrics'
        scrape_interval: 30s

  # Service configuration - NodePort for external access
  service:
    type: NodePort
    nodePort: 30090
    port: 9090

# Grafana configuration
grafana:
  # Enable Grafana
  enabled: true
  
  # Admin credentials
  adminPassword: "admin123"  # Change this in production!
  
  # Service configuration - NodePort for external access
  service:
    type: NodePort
    nodePort: 30030
    port: 80
  
  # Resource limits
  resources:
    requests:
      memory: "512Mi"
      cpu: "250m"
    limits:
      memory: "1Gi"
      cpu: "500m"
  
  # Persistence for dashboards
  persistence:
    enabled: true
    storageClassName: gp2
    size: 5Gi
  
  # Default dashboards
  defaultDashboardsEnabled: true
  
  # Additional datasources (Prometheus is auto-configured)
  additionalDataSources: []

# AlertManager configuration
alertmanager:
  alertmanagerSpec:
    # Resource limits
    resources:
      requests:
        memory: "256Mi"
        cpu: "100m"
      limits:
        memory: "512Mi"
        cpu: "200m"
  
  # Service configuration
  service:
    type: NodePort
    nodePort: 30093
    port: 9093

# Node Exporter configuration
nodeExporter:
  enabled: true

# kube-state-metrics configuration
kubeStateMetrics:
  enabled: true

# Prometheus Operator configuration
prometheusOperator:
  enabled: true
  
  # Resource limits for operator
  resources:
    requests:
      memory: "256Mi"
      cpu: "100m"
    limits:
      memory: "512Mi"
      cpu: "200m"

# Global configuration
global:
  rbac:
    create: true
    pspEnabled: false
```

### Step 2: Install kube-prometheus-stack

```bash
# Install the complete monitoring stack
helm install prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --values /home/prameshwar/Desktop/k8s/prometheus-values.yaml \
  --wait

# Verify installation
helm list -n monitoring

# Check if all pods are running
kubectl get pods -n monitoring
```

### Step 3: Verify Installation

```bash
# Check all resources created
kubectl get all -n monitoring

# Check persistent volumes
kubectl get pv
kubectl get pvc -n monitoring

# Check services with NodePorts
kubectl get svc -n monitoring | grep NodePort
```

## Grafana Installation with Helm

### Grafana is Already Included!

The `kube-prometheus-stack` Helm chart automatically installs Grafana with:
- Pre-configured Prometheus datasource
- Default Kubernetes dashboards
- NodePort service (port 30030)
- Persistent storage for dashboards

### Optional: Install Standalone Grafana

If you want a separate Grafana installation:

**File: `/home/prameshwar/Desktop/k8s/grafana-values.yaml`**
```yaml
# Admin credentials
adminUser: admin
adminPassword: admin123

# Service configuration
service:
  type: NodePort
  nodePort: 30031
  port: 80

# Persistence
persistence:
  enabled: true
  storageClassName: gp2
  size: 5Gi

# Resources
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "500m"

# Datasources
datasources:
  datasources.yaml:
    apiVersion: 1
    datasources:
    - name: Prometheus
      type: prometheus
      url: http://prometheus-stack-kube-prom-prometheus.monitoring.svc.cluster.local:9090
      access: proxy
      isDefault: true

# Default dashboards
dashboardProviders:
  dashboardproviders.yaml:
    apiVersion: 1
    providers:
    - name: 'default'
      orgId: 1
      folder: ''
      type: file
      disableDeletion: false
      editable: true
      options:
        path: /var/lib/grafana/dashboards/default

# Enable anonymous access (optional, for testing)
grafana.ini:
  auth.anonymous:
    enabled: false
  security:
    admin_user: admin
    admin_password: admin123
```

```bash
# Install standalone Grafana (optional)
helm install grafana grafana/grafana \
  --namespace monitoring \
  --values /home/prameshwar/Desktop/k8s/grafana-values.yaml \
  --wait
```
## Understanding Pods and Services

### What Gets Created by kube-prometheus-stack

When you install the Helm chart, it creates multiple pods and services. Let's understand each:

```bash
# List all pods created
kubectl get pods -n monitoring

# Expected output:
# NAME                                                     READY   STATUS    RESTARTS   AGE
# alertmanager-prometheus-stack-kube-prom-alertmanager-0   2/2     Running   0          5m
# prometheus-stack-grafana-xxx-xxx                         3/3     Running   0          5m
# prometheus-stack-kube-prom-operator-xxx-xxx              1/1     Running   0          5m
# prometheus-stack-kube-state-metrics-xxx-xxx              1/1     Running   0          5m
# prometheus-stack-prometheus-node-exporter-xxx            1/1     Running   0          5m
# prometheus-prometheus-stack-kube-prom-prometheus-0       2/2     Running   0          5m
```

### Detailed Pod Explanations

#### 1. Prometheus Pod (`prometheus-prometheus-stack-kube-prom-prometheus-0`)

**What it does:**
- **Metrics Collection**: Scrapes metrics from targets every 15-30 seconds
- **Data Storage**: Stores time-series data in TSDB format
- **Query Processing**: Executes PromQL queries for Grafana and alerts
- **Service Discovery**: Automatically finds new targets in Kubernetes
- **Rule Evaluation**: Processes alerting and recording rules

**Technical Details:**
```bash
# Describe the pod
kubectl describe pod -n monitoring prometheus-prometheus-stack-kube-prom-prometheus-0

# Key information:
# - Container: prometheus/prometheus:v2.45.0
# - Port: 9090 (web UI and API)
# - Volume Mounts: Config, storage, secrets
# - Resources: 2Gi memory, 1 CPU core
# - Probes: Liveness and readiness checks
```

**How it works:**
1. **Startup**: Reads configuration from mounted ConfigMap
2. **Discovery**: Uses Kubernetes API to find scrape targets
3. **Scraping**: HTTP GET requests to `/metrics` endpoints
4. **Storage**: Writes data to persistent volume in TSDB format
5. **Querying**: Serves PromQL queries via HTTP API

#### 2. Grafana Pod (`prometheus-stack-grafana-xxx-xxx`)

**What it does:**
- **Visualization**: Renders charts, graphs, and dashboards
- **Data Source Management**: Connects to Prometheus for data
- **User Interface**: Web-based dashboard creation and viewing
- **Alerting**: Visual alerts and notifications
- **Dashboard Storage**: Saves dashboards to persistent volume

**Technical Details:**
```bash
# Describe the pod
kubectl describe pod -n monitoring $(kubectl get pods -n monitoring -l app.kubernetes.io/name=grafana -o jsonpath='{.items[0].metadata.name}')

# Key information:
# - Container: grafana/grafana:10.0.0
# - Port: 3000 (web UI)
# - Init Containers: Setup and configuration
# - Sidecars: Dashboard and datasource provisioning
# - Resources: 1Gi memory, 500m CPU
```

**How it works:**
1. **Initialization**: Init containers set up configuration
2. **Startup**: Main container starts Grafana server
3. **Provisioning**: Sidecar containers load dashboards and datasources
4. **Data Fetching**: Queries Prometheus via HTTP API
5. **Rendering**: Converts data to visual charts and graphs

#### 3. AlertManager Pod (`alertmanager-prometheus-stack-kube-prom-alertmanager-0`)

**What it does:**
- **Alert Processing**: Receives alerts from Prometheus
- **Routing**: Sends alerts to correct destinations (email, Slack, etc.)
- **Grouping**: Combines similar alerts to reduce noise
- **Silencing**: Temporarily mutes alerts during maintenance
- **Inhibition**: Suppresses alerts based on other active alerts

**Technical Details:**
```bash
# Describe the pod
kubectl describe pod -n monitoring alertmanager-prometheus-stack-kube-prom-alertmanager-0

# Key information:
# - Container: alertmanager/alertmanager:v0.25.0
# - Port: 9093 (web UI and API)
# - StatefulSet: Maintains persistent identity
# - Resources: 512Mi memory, 200m CPU
```

#### 4. Node Exporter Pods (`prometheus-stack-prometheus-node-exporter-xxx`)

**What it does:**
- **System Metrics**: Collects hardware and OS metrics
- **Host Monitoring**: CPU, memory, disk, network statistics
- **File System**: Disk usage and mount point information
- **Process Stats**: Running processes and system load
- **Hardware Info**: Temperature, power, and hardware details

**Technical Details:**
```bash
# List node exporter pods (one per node)
kubectl get pods -n monitoring -l app.kubernetes.io/name=prometheus-node-exporter

# Key information:
# - DaemonSet: Runs on every node
# - Container: quay.io/prometheus/node-exporter:v1.6.0
# - Port: 9100 (metrics endpoint)
# - Host Network: Access to host system metrics
# - Privileged: Required for system access
```

#### 5. Kube-State-Metrics Pod (`prometheus-stack-kube-state-metrics-xxx-xxx`)

**What it does:**
- **Kubernetes Metrics**: Exposes cluster state as metrics
- **Resource Monitoring**: Pods, services, deployments, nodes
- **Status Information**: Ready/not ready, phase, conditions
- **Metadata**: Labels, annotations, resource versions
- **Capacity Planning**: Resource requests and limits

**Technical Details:**
```bash
# Describe the pod
kubectl describe pod -n monitoring $(kubectl get pods -n monitoring -l app.kubernetes.io/name=kube-state-metrics -o jsonpath='{.items[0].metadata.name}')

# Key information:
# - Container: registry.k8s.io/kube-state-metrics/kube-state-metrics:v2.9.2
# - Port: 8080 (metrics), 8081 (telemetry)
# - RBAC: Cluster-wide read permissions
# - Resources: 256Mi memory, 100m CPU
```

### Service Explanations

#### 1. Prometheus Services

```bash
# List Prometheus services
kubectl get svc -n monitoring | grep prometheus

# Expected services:
# prometheus-stack-kube-prom-prometheus    NodePort    10.100.x.x   <none>        9090:30090/TCP
# prometheus-stack-kube-prom-prometheus-headless ClusterIP None    <none>        9090/TCP
```

**NodePort Service (`prometheus-stack-kube-prom-prometheus`):**
```yaml
type: NodePort
ports:
- port: 9090        # Service port
  targetPort: 9090  # Pod port
  nodePort: 30090   # External port on nodes
```

**How it works:**
- **External Access**: `http://NODE_IP:30090`
- **Load Balancing**: Distributes traffic across Prometheus pods
- **Service Discovery**: Kubernetes DNS resolves service name
- **Health Checks**: Only routes to healthy pods

**Headless Service (`prometheus-stack-kube-prom-prometheus-headless`):**
```yaml
type: ClusterIP
clusterIP: None  # No cluster IP assigned
```
- **Purpose**: Direct pod-to-pod communication
- **StatefulSet**: Used by StatefulSet for stable network identity
- **DNS**: Returns individual pod IPs instead of service IP

#### 2. Grafana Services

```bash
# List Grafana services
kubectl get svc -n monitoring | grep grafana

# Expected service:
# prometheus-stack-grafana    NodePort    10.100.x.x   <none>        80:30030/TCP
```

**NodePort Service (`prometheus-stack-grafana`):**
```yaml
type: NodePort
ports:
- port: 80          # Service port
  targetPort: 3000  # Pod port (Grafana default)
  nodePort: 30030   # External port on nodes
```

**How it works:**
- **External Access**: `http://NODE_IP:30030`
- **Port Mapping**: Service port 80 → Pod port 3000
- **Session Affinity**: Can be configured for sticky sessions
- **Health Checks**: Routes only to ready Grafana pods

#### 3. AlertManager Services

```bash
# List AlertManager services
kubectl get svc -n monitoring | grep alertmanager

# Expected services:
# alertmanager-operated                    ClusterIP   None         <none>        9093/TCP,9094/TCP,9094/UDP
# prometheus-stack-kube-prom-alertmanager NodePort    10.100.x.x   <none>        9093:30093/TCP
```

**NodePort Service:**
- **External Access**: `http://NODE_IP:30093`
- **Web UI**: AlertManager dashboard and configuration
- **API Access**: For external alert routing configuration

### How Services Route Traffic

```
External Request (NODE_IP:30090)
         ↓
    NodePort Service
         ↓
    Service Selector (app=prometheus)
         ↓
    Healthy Pod Endpoints
         ↓
    Pod Container (port 9090)
```

### Resource Usage and Scaling

```bash
# Check resource usage
kubectl top pods -n monitoring

# Check resource requests and limits
kubectl describe pod -n monitoring prometheus-prometheus-stack-kube-prom-prometheus-0 | grep -A 10 "Requests\|Limits"

# Scale Grafana (if needed)
kubectl scale deployment prometheus-stack-grafana --replicas=2 -n monitoring
```

## Testing & Verification

### Step 1: Check Installation Status

```bash
# Check Helm release
helm list -n monitoring

# Expected output:
# NAME             NAMESPACE  REVISION  UPDATED                                  STATUS    CHART                       APP VERSION
# prometheus-stack monitoring 1         2024-08-12 10:30:00.000000000 +0000 UTC deployed  kube-prometheus-stack-51.2.0 v0.66.0

# Check all pods are running
kubectl get pods -n monitoring

# Check services with NodePorts
kubectl get svc -n monitoring | grep NodePort

# Expected NodePort services:
# prometheus-stack-kube-prom-prometheus    NodePort    10.100.x.x   <none>        9090:30090/TCP
# prometheus-stack-grafana                 NodePort    10.100.x.x   <none>        80:30030/TCP
# prometheus-stack-kube-prom-alertmanager  NodePort    10.100.x.x   <none>        9093:30093/TCP
```

### Step 2: Get Node IP for External Access

```bash
# Get external IP of any node
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="ExternalIP")].address}')

# If no external IP, use internal IP (for testing)
if [ -z "$NODE_IP" ]; then
    NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
fi

echo "Node IP: $NODE_IP"

# Access URLs:
echo "Prometheus: http://$NODE_IP:30090"
echo "Grafana: http://$NODE_IP:30030"
echo "AlertManager: http://$NODE_IP:30093"
```

### Step 3: Test Prometheus Access

```bash
# Method 1: Direct NodePort access
curl -s http://$NODE_IP:30090/api/v1/query?query=up | jq .

# Method 2: Port forward (alternative)
kubectl port-forward -n monitoring svc/prometheus-stack-kube-prom-prometheus 9090:9090 &
curl -s http://localhost:9090/api/v1/query?query=up | jq .

# Method 3: From within cluster
kubectl run test-pod --image=curlimages/curl -it --rm -- /bin/sh
# Inside the pod:
curl -s http://prometheus-stack-kube-prom-prometheus.monitoring.svc.cluster.local:9090/api/v1/query?query=up
```

### Step 4: Test Grafana Access

```bash
# Test Grafana health endpoint
curl -s http://$NODE_IP:30030/api/health

# Expected response:
# {"commit":"unknown","database":"ok","version":"10.0.0"}

# Test login page
curl -s http://$NODE_IP:30030/login | grep -o "<title>.*</title>"

# Expected: <title>Grafana</title>
```

### Step 5: Verify Data Flow

**Check Prometheus Targets:**
1. Open browser: `http://NODE_IP:30090`
2. Go to **Status → Targets**
3. Verify all targets are **UP**:
   - `prometheus-stack-kube-prom-prometheus`
   - `prometheus-stack-prometheus-node-exporter`
   - `prometheus-stack-kube-state-metrics`
   - Your finance app (if configured)

**Check Grafana Datasource:**
1. Open browser: `http://NODE_IP:30030`
2. Login: **admin / admin123**
3. Go to **Configuration → Data Sources**
4. Click **Prometheus** datasource
5. Click **Test** - should show "Data source is working"

## Metrics Testing Guide

### Basic Prometheus Queries

Open Prometheus UI (`http://NODE_IP:30090`) and test these queries:

#### 1. System Health Queries

```promql
# Check if all targets are up
up

# Count of up targets by job
count by (job) (up == 1)

# Prometheus server uptime
time() - process_start_time_seconds{job="prometheus-stack-kube-prom-prometheus"}

# Scrape duration (how long it takes to collect metrics)
prometheus_target_scrape_duration_seconds
```

#### 2. Node/System Metrics

```promql
# CPU usage per node (percentage)
100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Memory usage per node (percentage)
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100

# Disk usage per node (percentage)
100 - ((node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100)

# Network traffic (bytes per second)
rate(node_network_receive_bytes_total[5m])
rate(node_network_transmit_bytes_total[5m])

# Load average
node_load1
node_load5
node_load15
```

#### 3. Kubernetes Cluster Metrics

```promql
# Number of pods by namespace
count by (namespace) (kube_pod_info)

# Pods not in Running state
kube_pod_status_phase{phase!="Running"}

# Node capacity and allocatable resources
kube_node_status_capacity
kube_node_status_allocatable

# Pod resource requests vs limits
kube_pod_container_resource_requests
kube_pod_container_resource_limits

# Deployment replicas vs available replicas
kube_deployment_status_replicas
kube_deployment_status_replicas_available
```

#### 4. Container Metrics

```promql
# Container CPU usage
rate(container_cpu_usage_seconds_total[5m])

# Container memory usage
container_memory_usage_bytes

# Container restart count
kube_pod_container_status_restarts_total

# Container states
kube_pod_container_status_running
kube_pod_container_status_waiting
kube_pod_container_status_terminated
```

### Advanced Prometheus Queries

#### 1. Alerting Queries

```promql
# High CPU usage alert
100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80

# High memory usage alert
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85

# Pod crash looping
rate(kube_pod_container_status_restarts_total[15m]) > 0

# Node not ready
kube_node_status_condition{condition="Ready",status="false"} == 1
```

#### 2. Capacity Planning Queries

```promql
# CPU request vs capacity
sum(kube_pod_container_resource_requests{resource="cpu"}) / sum(kube_node_status_allocatable{resource="cpu"}) * 100

# Memory request vs capacity
sum(kube_pod_container_resource_requests{resource="memory"}) / sum(kube_node_status_allocatable{resource="memory"}) * 100

# Predicted disk full time (linear regression)
predict_linear(node_filesystem_avail_bytes{mountpoint="/"}[1h], 24*3600)
```

#### 3. Performance Queries

```promql
# Top 10 CPU consuming pods
topk(10, rate(container_cpu_usage_seconds_total{container!="POD",container!=""}[5m]))

# Top 10 memory consuming pods
topk(10, container_memory_usage_bytes{container!="POD",container!=""})

# Network I/O by pod
sum by (pod) (rate(container_network_receive_bytes_total[5m]))
sum by (pod) (rate(container_network_transmit_bytes_total[5m]))
```

### Testing Your Finance App Metrics

If you've added metrics to your finance app, test these queries:

```promql
# Check if your app is being scraped
up{job="finance-app"}

# Request rate
rate(flask_requests_total[5m])

# Error rate
rate(flask_requests_total{status=~"5.."}[5m]) / rate(flask_requests_total[5m])

# Response time percentiles
histogram_quantile(0.50, rate(flask_request_duration_seconds_bucket[5m]))
histogram_quantile(0.95, rate(flask_request_duration_seconds_bucket[5m]))
histogram_quantile(0.99, rate(flask_request_duration_seconds_bucket[5m]))

# Business metrics (if implemented)
finance_app_transactions_total
finance_app_active_users
```
## Query Examples

### Grafana Dashboard Creation

#### 1. Access Grafana
1. Open browser: `http://NODE_IP:30030`
2. Login: **admin / admin123**
3. Click **"+"** → **Dashboard** → **Add new panel**

#### 2. Basic Queries for Your Finance App

**Panel 1: Application Uptime**
```promql
# Query:
up{job="finance-app"}

# Visualization: Stat
# Title: "Finance App Status"
# Value mappings: 0 = Down (Red), 1 = Up (Green)
```

**Panel 2: Request Rate**
```promql
# Query:
sum(rate(flask_requests_total[5m]))

# Visualization: Graph
# Title: "Requests per Second"
# Y-axis: Requests/sec
```

**Panel 3: Error Rate**
```promql
# Query:
sum(rate(flask_requests_total{status=~"5.."}[5m])) / sum(rate(flask_requests_total[5m])) * 100

# Visualization: Graph
# Title: "Error Rate (%)"
# Y-axis: Percentage
# Thresholds: Warning > 1%, Critical > 5%
```

**Panel 4: Response Time**
```promql
# Query:
histogram_quantile(0.95, sum(rate(flask_request_duration_seconds_bucket[5m])) by (le))

# Visualization: Graph
# Title: "95th Percentile Response Time"
# Y-axis: Seconds
```

#### 3. System Monitoring Queries

**Panel 5: CPU Usage**
```promql
# Query:
100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Visualization: Graph
# Title: "Node CPU Usage (%)"
# Y-axis: Percentage (0-100)
```

**Panel 6: Memory Usage**
```promql
# Query:
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100

# Visualization: Graph
# Title: "Node Memory Usage (%)"
# Y-axis: Percentage (0-100)
```

**Panel 7: Pod Status**
```promql
# Query:
count by (phase) (kube_pod_status_phase{namespace="finance-tracker"})

# Visualization: Pie chart
# Title: "Pod Status Distribution"
```

#### 4. Kubernetes Cluster Queries

**Panel 8: Cluster Resource Usage**
```promql
# CPU Query:
sum(kube_pod_container_resource_requests{resource="cpu"}) / sum(kube_node_status_allocatable{resource="cpu"}) * 100

# Memory Query:
sum(kube_pod_container_resource_requests{resource="memory"}) / sum(kube_node_status_allocatable{resource="memory"}) * 100

# Visualization: Gauge
# Title: "Cluster Resource Utilization"
```

### Advanced Query Examples

#### 1. Business Logic Queries (for your Finance App)

```promql
# Total transactions per hour
increase(finance_app_transactions_total[1h])

# Transaction rate by type
sum by (type) (rate(finance_app_transactions_total[5m]))

# Average account balance
avg(finance_app_account_balance)

# Active users over time
finance_app_active_users

# Top spending categories
topk(5, sum by (category) (rate(finance_app_transactions_total{type="expense"}[1h])))
```

#### 2. Performance Analysis Queries

```promql
# Request latency by endpoint
histogram_quantile(0.95, sum(rate(flask_request_duration_seconds_bucket[5m])) by (endpoint, le))

# Requests by HTTP method
sum by (method) (rate(flask_requests_total[5m]))

# Error rate by endpoint
sum by (endpoint) (rate(flask_requests_total{status=~"5.."}[5m])) / sum by (endpoint) (rate(flask_requests_total[5m]))

# Concurrent requests
flask_requests_active
```

#### 3. Infrastructure Monitoring Queries

```promql
# Disk I/O
rate(node_disk_read_bytes_total[5m])
rate(node_disk_written_bytes_total[5m])

# Network traffic
rate(node_network_receive_bytes_total[5m])
rate(node_network_transmit_bytes_total[5m])

# Container restarts
increase(kube_pod_container_status_restarts_total[1h])

# Pod scheduling time
histogram_quantile(0.95, sum(rate(scheduler_scheduling_duration_seconds_bucket[5m])) by (le))
```

### Testing Queries Step by Step

#### 1. Test in Prometheus First

Before creating Grafana panels, test queries in Prometheus:

1. **Open Prometheus**: `http://NODE_IP:30090`
2. **Go to Graph tab**
3. **Enter query**: `up`
4. **Click Execute**
5. **Verify results**: Should show all monitored targets

#### 2. Common Query Patterns

**Rate Calculations:**
```promql
# Per-second rate over 5 minutes
rate(metric_name[5m])

# Per-second rate with sum
sum(rate(metric_name[5m]))

# Rate by label
sum by (label_name) (rate(metric_name[5m]))
```

**Aggregations:**
```promql
# Sum all values
sum(metric_name)

# Average by instance
avg by (instance) (metric_name)

# Maximum value
max(metric_name)

# Count of series
count(metric_name)
```

**Time-based Functions:**
```promql
# Increase over time window
increase(metric_name[1h])

# Delta (difference)
delta(metric_name[5m])

# Derivative (rate of change)
deriv(metric_name[5m])
```

#### 3. Troubleshooting Queries

**No Data Issues:**
```promql
# Check if target is up
up{job="your-job-name"}

# Check scrape duration
prometheus_target_scrape_duration_seconds{job="your-job-name"}

# Check for scrape errors
up{job="your-job-name"} == 0
```

**Performance Issues:**
```promql
# Query execution time
prometheus_engine_query_duration_seconds

# Number of samples processed
prometheus_engine_query_samples_total

# Memory usage
process_resident_memory_bytes{job="prometheus-stack-kube-prom-prometheus"}
```

### Creating Alerts in Grafana

#### 1. Simple Alert Rules

**High CPU Alert:**
```promql
# Query:
100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80

# Condition: IS ABOVE 80
# Evaluation: Every 1m for 2m
```

**Application Down Alert:**
```promql
# Query:
up{job="finance-app"} == 0

# Condition: IS EQUAL TO 0
# Evaluation: Every 30s for 1m
```

**High Error Rate Alert:**
```promql
# Query:
sum(rate(flask_requests_total{status=~"5.."}[5m])) / sum(rate(flask_requests_total[5m])) * 100 > 5

# Condition: IS ABOVE 5
# Evaluation: Every 1m for 2m
```

#### 2. Setting Up Notifications

1. **Go to Alerting → Notification channels**
2. **Add channel** (Email, Slack, etc.)
3. **Test notification**
4. **Assign to alert rules**

### Performance Optimization

#### 1. Query Optimization

**Efficient Queries:**
```promql
# Good: Specific job filter
rate(flask_requests_total{job="finance-app"}[5m])

# Bad: No filters (scans all metrics)
rate(flask_requests_total[5m])

# Good: Aggregate first, then calculate
sum(rate(metric[5m])) by (instance)

# Bad: Calculate then aggregate
sum(rate(metric[5m]) by (instance))
```

#### 2. Dashboard Performance

- **Limit time ranges**: Use shorter ranges for real-time dashboards
- **Reduce refresh rates**: Don't refresh every 5 seconds unless needed
- **Use recording rules**: Pre-calculate complex queries
- **Limit series**: Use topk() to limit high-cardinality metrics

### Complete Testing Checklist

```bash
# 1. Verify all components are running
kubectl get pods -n monitoring

# 2. Test Prometheus access
curl -s http://$NODE_IP:30090/api/v1/query?query=up

# 3. Test Grafana access
curl -s http://$NODE_IP:30030/api/health

# 4. Check targets in Prometheus UI
# Go to Status → Targets, verify all are UP

# 5. Test Grafana datasource
# Configuration → Data Sources → Prometheus → Test

# 6. Create test dashboard
# + → Dashboard → Add panel → Query: up

# 7. Test alerting (optional)
# Create alert rule with simple condition

# 8. Verify metrics from your app
curl -s http://finance-app-service.finance-tracker.svc.cluster.local/metrics
```

This comprehensive guide provides everything you need to install, configure, and test Prometheus and Grafana using Helm charts, with detailed explanations of how each component works and extensive query examples for monitoring your personal finance tracker application.

## Dashboards

### Pre-built Dashboards

The kube-prometheus-stack comes with many pre-built dashboards:

1. **Access Grafana**: `http://NODE_IP:30030` (admin/admin123)
2. **Browse Dashboards**: Click **Dashboards** → **Browse**
3. **Available Dashboards**:
   - **Kubernetes / Compute Resources / Cluster**
   - **Kubernetes / Compute Resources / Namespace (Pods)**
   - **Kubernetes / Compute Resources / Node (Pods)**
   - **Node Exporter / Nodes**
   - **Prometheus / Overview**

### Import Additional Dashboards

#### 1. Popular Community Dashboards

**Node Exporter Full Dashboard:**
- Dashboard ID: **1860**
- Go to **"+" → Import → Enter ID: 1860**

**Kubernetes Cluster Monitoring:**
- Dashboard ID: **315**
- Go to **"+" → Import → Enter ID: 315**

**NGINX Ingress Controller:**
- Dashboard ID: **9614**
- Go to **"+" → Import → Enter ID: 9614**

#### 2. Custom Finance App Dashboard

**Create Custom Dashboard JSON:**

**File: `/home/prameshwar/Desktop/k8s/finance-app-dashboard.json`**
```json
{
  "dashboard": {
    "id": null,
    "title": "Personal Finance Tracker Monitoring",
    "tags": ["finance", "application"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Application Status",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"finance-app\"}",
            "legendFormat": "App Status"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "mappings": [
              {
                "options": {
                  "0": {
                    "text": "DOWN",
                    "color": "red"
                  },
                  "1": {
                    "text": "UP",
                    "color": "green"
                  }
                },
                "type": "value"
              }
            ]
          }
        },
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 0,
          "y": 0
        }
      },
      {
        "id": 2,
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(flask_requests_total[5m]))",
            "legendFormat": "Requests/sec"
          }
        ],
        "yAxes": [
          {
            "label": "Requests per second"
          }
        ],
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 12,
          "y": 0
        }
      },
      {
        "id": 3,
        "title": "Response Time (95th percentile)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(flask_request_duration_seconds_bucket[5m])) by (le))",
            "legendFormat": "95th percentile"
          }
        ],
        "yAxes": [
          {
            "label": "Seconds"
          }
        ],
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 0,
          "y": 8
        }
      },
      {
        "id": 4,
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(flask_requests_total{status=~\"5..\"}[5m])) / sum(rate(flask_requests_total[5m])) * 100",
            "legendFormat": "Error Rate %"
          }
        ],
        "yAxes": [
          {
            "label": "Percentage"
          }
        ],
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 12,
          "y": 8
        }
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "30s"
  }
}
```

**Import Custom Dashboard:**
1. Copy the JSON content
2. Go to **"+" → Import**
3. Paste JSON in **"Import via panel json"**
4. Click **Load**

## Troubleshooting

### Common Issues and Solutions

#### 1. Helm Installation Fails

**Error: "repository name (prometheus-community) already exists"**
```bash
# Solution: Update existing repo
helm repo update prometheus-community
```

**Error: "namespace monitoring not found"**
```bash
# Solution: Create namespace first
kubectl create namespace monitoring
```

**Error: "insufficient resources"**
```bash
# Solution: Check node resources
kubectl describe nodes
kubectl top nodes

# Reduce resource requests in values file
prometheus:
  prometheusSpec:
    resources:
      requests:
        memory: "512Mi"  # Reduced from 1Gi
        cpu: "250m"      # Reduced from 500m
```

#### 2. Pods Not Starting

**CrashLoopBackOff Status:**
```bash
# Check pod logs
kubectl logs -n monitoring <pod-name>

# Check pod events
kubectl describe pod -n monitoring <pod-name>

# Common causes:
# - Insufficient resources
# - Configuration errors
# - Storage issues
```

**Pending Status:**
```bash
# Check why pod is pending
kubectl describe pod -n monitoring <pod-name>

# Common causes:
# - No available nodes
# - Resource constraints
# - Storage class issues
```

#### 3. NodePort Not Accessible

**Connection Refused:**
```bash
# Check if service exists
kubectl get svc -n monitoring | grep NodePort

# Check node IP
kubectl get nodes -o wide

# Check security groups (AWS)
# Ensure ports 30090, 30030, 30093 are open

# Test from within cluster
kubectl run test-pod --image=curlimages/curl -it --rm -- /bin/sh
curl http://prometheus-stack-kube-prom-prometheus.monitoring.svc.cluster.local:9090
```

#### 4. No Metrics Data

**Targets Down in Prometheus:**
```bash
# Check service discovery
kubectl get endpoints -n monitoring

# Check RBAC permissions
kubectl auth can-i get pods --as=system:serviceaccount:monitoring:prometheus-stack-kube-prom-prometheus

# Check network policies
kubectl get networkpolicies -A
```

**Grafana Shows "No Data":**
```bash
# Test Prometheus datasource
curl -s http://NODE_IP:30090/api/v1/query?query=up

# Check Grafana logs
kubectl logs -n monitoring deployment/prometheus-stack-grafana

# Verify datasource configuration
kubectl get configmap -n monitoring prometheus-stack-grafana -o yaml
```

#### 5. Performance Issues

**High Memory Usage:**
```bash
# Check resource usage
kubectl top pods -n monitoring

# Reduce retention time
helm upgrade prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --set prometheus.prometheusSpec.retention=7d
```

**Slow Queries:**
```bash
# Check query performance in Prometheus
# Go to Status → Runtime & Build Information
# Look for "Query log enabled"

# Optimize queries:
# - Add more specific label filters
# - Use recording rules for complex queries
# - Reduce time ranges
```

### Monitoring the Monitoring Stack

#### Health Check Queries

```promql
# Prometheus health
up{job="prometheus-stack-kube-prom-prometheus"}

# Grafana health
up{job="prometheus-stack-grafana"}

# AlertManager health
up{job="prometheus-stack-kube-prom-alertmanager"}

# Node Exporter health
up{job="prometheus-stack-prometheus-node-exporter"}

# Kube-state-metrics health
up{job="prometheus-stack-kube-state-metrics"}
```

#### Performance Monitoring

```promql
# Prometheus memory usage
process_resident_memory_bytes{job="prometheus-stack-kube-prom-prometheus"}

# Query duration
prometheus_engine_query_duration_seconds

# Scrape duration
prometheus_target_scrape_duration_seconds

# Failed scrapes
prometheus_target_scrapes_exceeded_sample_limit_total
```

### Complete Deployment Script

**File: `/home/prameshwar/Desktop/k8s/deploy-monitoring-helm.sh`**
```bash
#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Deploying Monitoring Stack with Helm${NC}"
echo "=================================================="

# Check if Helm is installed
if ! command -v helm &> /dev/null; then
    echo -e "${RED}❌ Helm is not installed. Please install Helm first.${NC}"
    exit 1
fi

# Create monitoring namespace
echo -e "${YELLOW}📁 Creating monitoring namespace...${NC}"
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

# Add Helm repositories
echo -e "${YELLOW}📦 Adding Helm repositories...${NC}"
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install kube-prometheus-stack
echo -e "${YELLOW}📊 Installing kube-prometheus-stack...${NC}"
helm install prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --values prometheus-values.yaml \
  --wait \
  --timeout 10m

# Wait for all pods to be ready
echo -e "${YELLOW}⏳ Waiting for all pods to be ready...${NC}"
kubectl wait --for=condition=ready pod --all -n monitoring --timeout=300s

# Get node IP
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="ExternalIP")].address}')
if [ -z "$NODE_IP" ]; then
    NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
fi

# Show status
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo -e "${BLUE}📋 Status:${NC}"
kubectl get pods -n monitoring
echo ""
kubectl get svc -n monitoring | grep NodePort
echo ""

# Show access information
echo -e "${BLUE}🔗 Access Information:${NC}"
echo "=================================================="
echo -e "${GREEN}Prometheus:${NC}"
echo "  URL: http://$NODE_IP:30090"
echo "  Status → Targets to verify scraping"
echo ""
echo -e "${GREEN}Grafana:${NC}"
echo "  URL: http://$NODE_IP:30030"
echo "  Username: admin"
echo "  Password: admin123"
echo "  Pre-built dashboards available in Browse section"
echo ""
echo -e "${GREEN}AlertManager:${NC}"
echo "  URL: http://$NODE_IP:30093"
echo ""

echo -e "${YELLOW}📚 Next Steps:${NC}"
echo "1. Access Grafana and explore pre-built dashboards"
echo "2. Import additional dashboards (IDs: 1860, 315, 9614)"
echo "3. Add metrics endpoint to your finance app"
echo "4. Create custom dashboards for your application"
echo "5. Set up alerting rules and notification channels"
echo ""

echo -e "${BLUE}🔧 Troubleshooting:${NC}"
echo "  Check pods: kubectl get pods -n monitoring"
echo "  Check logs: kubectl logs -n monitoring <pod-name>"
echo "  Check services: kubectl get svc -n monitoring"
echo "  Port forward: kubectl port-forward -n monitoring svc/prometheus-stack-kube-prom-prometheus 9090:9090"
```

**Make script executable and run:**
```bash
chmod +x /home/prameshwar/Desktop/k8s/deploy-monitoring-helm.sh
cd /home/prameshwar/Desktop/k8s
./deploy-monitoring-helm.sh
```

This comprehensive guide provides everything you need to successfully deploy and manage Prometheus and Grafana using Helm charts, with detailed explanations of all components and extensive testing procedures.
## Complete Deployment Script

**File: `/home/prameshwar/Desktop/k8s/deploy-monitoring.sh`**
```bash
#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Deploying Monitoring Stack for Personal Finance Tracker${NC}"
echo "=================================================================="

# Create monitoring namespace
echo -e "${YELLOW}📁 Creating monitoring namespace...${NC}"
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

# Deploy Prometheus
echo -e "${YELLOW}📊 Deploying Prometheus...${NC}"
kubectl apply -f prometheus-rbac.yaml
kubectl apply -f prometheus-config.yaml
kubectl apply -f prometheus-deployment.yaml
kubectl apply -f prometheus-service.yaml

# Wait for Prometheus to be ready
echo -e "${YELLOW}⏳ Waiting for Prometheus to be ready...${NC}"
kubectl wait --for=condition=available --timeout=300s deployment/prometheus -n monitoring

# Deploy Grafana
echo -e "${YELLOW}📈 Deploying Grafana...${NC}"
kubectl apply -f grafana-config.yaml
kubectl apply -f grafana-deployment.yaml
kubectl apply -f grafana-service.yaml

# Wait for Grafana to be ready
echo -e "${YELLOW}⏳ Waiting for Grafana to be ready...${NC}"
kubectl wait --for=condition=available --timeout=300s deployment/grafana -n monitoring

# Deploy monitoring ingress (optional)
if [ -f "monitoring-ingress.yaml" ]; then
    echo -e "${YELLOW}🌐 Deploying monitoring ingress...${NC}"
    kubectl apply -f monitoring-ingress.yaml
fi

# Show status
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo -e "${BLUE}📋 Status:${NC}"
kubectl get pods -n monitoring
echo ""
kubectl get svc -n monitoring
echo ""

# Show access information
echo -e "${BLUE}🔗 Access Information:${NC}"
echo "=================================================================="
echo -e "${GREEN}Prometheus:${NC}"
echo "  Port Forward: kubectl port-forward -n monitoring svc/prometheus-service 9090:9090"
echo "  URL: http://localhost:9090"
echo ""
echo -e "${GREEN}Grafana:${NC}"
echo "  Port Forward: kubectl port-forward -n monitoring svc/grafana-service 3000:3000"
echo "  URL: http://localhost:3000"
echo "  Username: admin"
echo "  Password: admin123"
echo ""

# Check if NodePort services exist
if kubectl get svc -n monitoring prometheus-nodeport >/dev/null 2>&1; then
    NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="ExternalIP")].address}')
    if [ -z "$NODE_IP" ]; then
        NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
    fi
    echo -e "${GREEN}NodePort Access:${NC}"
    echo "  Prometheus: http://$NODE_IP:30090"
    echo "  Grafana: http://$NODE_IP:30030"
fi

echo ""
echo -e "${YELLOW}📚 Next Steps:${NC}"
echo "1. Access Grafana and verify Prometheus data source"
echo "2. Import dashboard ID 315 for Kubernetes monitoring"
echo "3. Add metrics endpoint to your finance app"
echo "4. Create custom dashboards for your application"
echo ""
echo -e "${BLUE}🔧 Troubleshooting:${NC}"
echo "  Check logs: kubectl logs -n monitoring deployment/prometheus"
echo "  Check logs: kubectl logs -n monitoring deployment/grafana"
echo "  Check events: kubectl get events -n monitoring --sort-by='.lastTimestamp'"
```

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. Prometheus Pod Not Starting

**Symptoms:**
```bash
kubectl get pods -n monitoring
# prometheus-xxx-xxx   0/1     CrashLoopBackOff   3          2m
```

**Diagnosis:**
```bash
kubectl logs -n monitoring deployment/prometheus
kubectl describe pod -n monitoring <prometheus-pod-name>
```

**Common Causes & Solutions:**

**A. Configuration Error:**
```bash
# Check config syntax
kubectl get configmap -n monitoring prometheus-config -o yaml
# Fix any YAML syntax errors in prometheus-config.yaml
```

**B. RBAC Issues:**
```bash
# Verify service account
kubectl get sa -n monitoring prometheus
# Verify cluster role binding
kubectl get clusterrolebinding prometheus
```

**C. Resource Limits:**
```bash
# Check node resources
kubectl top nodes
# Reduce resource requests in prometheus-deployment.yaml
```

#### 2. Grafana Pod Not Starting

**Symptoms:**
```bash
kubectl get pods -n monitoring
# grafana-xxx-xxx   0/1     Pending   0          2m
```

**Diagnosis:**
```bash
kubectl describe pod -n monitoring <grafana-pod-name>
kubectl logs -n monitoring deployment/grafana
```

**Common Solutions:**

**A. Permission Issues:**
```bash
# Check if fsGroup is set correctly
# Ensure securityContext in grafana-deployment.yaml:
securityContext:
  fsGroup: 472
  supplementalGroups:
    - 0
```

**B. Volume Mount Issues:**
```bash
# Check if volumes are properly defined
# Verify configmap exists
kubectl get configmap -n monitoring grafana-datasources
```

#### 3. Metrics Not Appearing

**Symptoms:**
- Prometheus UI shows targets as "DOWN"
- No data in Grafana dashboards

**Diagnosis:**
```bash
# Check Prometheus targets
kubectl port-forward -n monitoring svc/prometheus-service 9090:9090
# Go to http://localhost:9090/targets

# Test service connectivity
kubectl run test-pod --image=curlimages/curl -it --rm -- /bin/sh
curl http://prometheus-service.monitoring.svc.cluster.local:9090/api/v1/query?query=up
```

**Solutions:**

**A. Service Discovery Issues:**
```bash
# Check if RBAC allows Prometheus to discover services
kubectl auth can-i get pods --as=system:serviceaccount:monitoring:prometheus
kubectl auth can-i list services --as=system:serviceaccount:monitoring:prometheus
```

**B. Network Policies:**
```bash
# Check if network policies are blocking traffic
kubectl get networkpolicies -A
```

**C. Target Configuration:**
```bash
# Verify target endpoints exist
kubectl get endpoints -n finance-tracker finance-app-service
```

#### 4. Grafana Can't Connect to Prometheus

**Symptoms:**
- Grafana shows "Data source is not working"
- Connection timeout errors

**Solutions:**

**A. Check Service Names:**
```bash
# Verify Prometheus service exists
kubectl get svc -n monitoring prometheus-service

# Test connectivity from Grafana pod
kubectl exec -n monitoring deployment/grafana -- curl http://prometheus-service.monitoring.svc.cluster.local:9090/api/v1/query?query=up
```

**B. Update Datasource Configuration:**
```yaml
# In grafana-config.yaml, ensure URL is correct:
"url": "http://prometheus-service.monitoring.svc.cluster.local:9090"
```

### Performance Tuning

#### Prometheus Optimization

**For Large Clusters:**
```yaml
# In prometheus-deployment.yaml
args:
  - '--storage.tsdb.retention.time=15d'  # Reduce retention
  - '--storage.tsdb.retention.size=10GB'  # Add size limit
  - '--query.max-concurrency=20'         # Limit concurrent queries
  - '--query.max-samples=50000000'       # Limit query samples
```

**Resource Adjustments:**
```yaml
resources:
  requests:
    cpu: 500m      # Increase for large clusters
    memory: 2Gi    # Increase for more metrics
  limits:
    cpu: 2000m
    memory: 4Gi
```

#### Grafana Optimization

**For Better Performance:**
```yaml
env:
- name: GF_DATABASE_TYPE
  value: sqlite3
- name: GF_DATABASE_PATH
  value: /var/lib/grafana/grafana.db
- name: GF_ANALYTICS_REPORTING_ENABLED
  value: "false"
- name: GF_ANALYTICS_CHECK_FOR_UPDATES
  value: "false"
```

## Security Considerations

### Production Security Checklist

#### 1. Change Default Passwords
```bash
# Generate secure password
GRAFANA_PASSWORD=$(openssl rand -base64 32)

# Create secret
kubectl create secret generic grafana-credentials \
  --from-literal=admin-password=$GRAFANA_PASSWORD \
  -n monitoring

# Update deployment to use secret
env:
- name: GF_SECURITY_ADMIN_PASSWORD
  valueFrom:
    secretKeyRef:
      name: grafana-credentials
      key: admin-password
```

#### 2. Enable HTTPS
```yaml
# Add to monitoring-ingress.yaml
metadata:
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - grafana.yourdomain.com
    - prometheus.yourdomain.com
    secretName: monitoring-tls
```

#### 3. Restrict Access
```yaml
# Add authentication to ingress
metadata:
  annotations:
    nginx.ingress.kubernetes.io/auth-type: basic
    nginx.ingress.kubernetes.io/auth-secret: basic-auth
    nginx.ingress.kubernetes.io/auth-realm: 'Authentication Required'
```

#### 4. Network Policies
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: monitoring-network-policy
  namespace: monitoring
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: finance-tracker
```

## Monitoring Best Practices

### 1. Alerting Rules

**File: `/home/prameshwar/Desktop/k8s/prometheus-alerts.yaml`**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-alerts
  namespace: monitoring
data:
  alerts.yml: |
    groups:
    - name: finance-app-alerts
      rules:
      - alert: FinanceAppDown
        expr: up{job="finance-app"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Finance app is down"
          description: "Finance app has been down for more than 1 minute"
      
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(flask_request_duration_seconds_bucket[5m])) > 1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High response time"
          description: "95th percentile response time is above 1 second"
      
      - alert: HighErrorRate
        expr: rate(flask_requests_total{status=~"5.."}[5m]) > 0.1
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "High error rate"
          description: "Error rate is above 10%"
```

### 2. Backup Strategy

```bash
# Backup Grafana dashboards
kubectl exec -n monitoring deployment/grafana -- sqlite3 /var/lib/grafana/grafana.db .dump > grafana-backup.sql

# Backup Prometheus data (if using persistent storage)
kubectl exec -n monitoring deployment/prometheus -- tar czf - /prometheus > prometheus-backup.tar.gz
```

### 3. Monitoring the Monitoring

```promql
# Prometheus health
up{job="prometheus"}

# Grafana health
up{job="grafana"}

# Scrape duration
prometheus_target_scrape_duration_seconds

# Failed scrapes
prometheus_target_scrapes_exceeded_sample_limit_total
```

This comprehensive guide provides everything you need to set up, deploy, and maintain a robust monitoring solution for your Personal Finance Tracker application on EKS. The monitoring stack will give you insights into both your application performance and Kubernetes cluster health.
