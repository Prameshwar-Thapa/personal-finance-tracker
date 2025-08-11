# Personal Finance Tracker - Kubernetes Architecture Diagram

## High-Level Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                 MINIKUBE NODE                                   │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                          finance-app NAMESPACE                          │   │
│  │                                                                         │   │
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐     │   │
│  │  │   SERVICES      │    │  CONFIGURATION  │    │   STORAGE       │     │   │
│  │  │                 │    │                 │    │                 │     │   │
│  │  │ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │     │   │
│  │  │ │ NodePort    │ │    │ │ ConfigMap   │ │    │ │PostgreSQL PV│ │     │   │
│  │  │ │ :30080      │ │    │ │(Non-secret) │ │    │ │    5Gi      │ │     │   │
│  │  │ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │     │   │
│  │  │                 │    │                 │    │                 │     │   │
│  │  │ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │     │   │
│  │  │ │PostgreSQL   │ │    │ │   Secret    │ │    │ │ Uploads PV  │ │     │   │
│  │  │ │Service      │ │    │ │(Passwords)  │ │    │ │    2Gi      │ │     │   │
│  │  │ │(Headless)   │ │    │ └─────────────┘ │    │ └─────────────┘ │     │   │
│  │  │ └─────────────┘ │    └─────────────────┘    └─────────────────┘     │   │
│  │  │                 │                                                   │   │
│  │  │ ┌─────────────┐ │                                                   │   │
│  │  │ │Redis Service│ │                                                   │   │
│  │  │ │(ClusterIP)  │ │                                                   │   │
│  │  │ └─────────────┘ │                                                   │   │
│  │  └─────────────────┘                                                   │   │
│  │                                                                         │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │   │
│  │  │                        APPLICATION LAYER                        │   │   │
│  │  │                                                                 │   │   │
│  │  │  ┌─────────────────────────────────────────────────────────┐   │   │   │
│  │  │  │              Flask App (Deployment)                     │   │   │   │
│  │  │  │                                                         │   │   │   │
│  │  │  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │   │   │   │
│  │  │  │  │    Init     │    │  App Pod 1  │    │  App Pod 2  │ │   │   │   │
│  │  │  │  │ Container   │    │   (Flask)   │    │   (Flask)   │ │   │   │   │
│  │  │  │  │(Wait for DB)│    │             │    │             │ │   │   │   │
│  │  │  │  └─────────────┘    └─────────────┘    └─────────────┘ │   │   │   │
│  │  │  └─────────────────────────────────────────────────────────┘   │   │   │
│  │  └─────────────────────────────────────────────────────────────────┘   │   │
│  │                                                                         │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │   │
│  │  │                         DATA LAYER                              │   │   │
│  │  │                                                                 │   │   │
│  │  │  ┌─────────────────────┐    ┌─────────────────────────────────┐ │   │   │
│  │  │  │PostgreSQL StatefulSet│    │      Redis Deployment          │ │   │   │
│  │  │  │                     │    │                                 │ │   │   │
│  │  │  │  ┌─────────────┐    │    │  ┌─────────────┐                │ │   │   │
│  │  │  │  │ postgres-0  │    │    │  │ Redis Pod   │                │ │   │   │
│  │  │  │  │(Primary DB) │    │    │  │  (Cache)    │                │ │   │   │
│  │  │  │  └─────────────┘    │    │  └─────────────┘                │ │   │   │
│  │  │  └─────────────────────┘    └─────────────────────────────────┘ │   │   │
│  │  └─────────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                           HOST STORAGE                                  │   │
│  │                                                                         │   │
│  │  ┌─────────────────┐              ┌─────────────────┐                  │   │
│  │  │  /data/postgres │              │  /data/uploads  │                  │   │
│  │  │   (hostPath)    │              │   (hostPath)    │                  │   │
│  │  └─────────────────┘              └─────────────────┘                  │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘

                                        ▲
                                        │
                                ┌───────┴───────┐
                                │ User/Browser  │
                                │ (External)    │
                                └───────────────┘
```

## Detailed Component Flow

### 1. External Access Flow
```
User/Browser → Minikube Node IP:30080 → NodePort Service → Flask App Pods
```

### 2. Application Internal Communication
```
Flask App Pods → PostgreSQL Service → postgres-0 Pod
Flask App Pods → Redis Service → Redis Pod
```

### 3. Storage Flow
```
postgres-0 Pod → PostgreSQL PVC → PostgreSQL PV → /data/postgres (hostPath)
Flask App Pods → Uploads PVC → Uploads PV → /data/uploads (hostPath)
```

### 4. Configuration Injection
```
ConfigMap → Environment Variables → All Pods
Secret → Sensitive Data → All Pods
```

## Network Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        NETWORK LAYER                            │
│                                                                 │
│  External Traffic (Port 30080)                                 │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                           │
│  │ NodePort Service│ ──────────────┐                          │
│  │ (finance-app-   │               │                          │
│  │  nodeport)      │               │                          │
│  └─────────────────┘               │                          │
│                                    │                          │
│  Internal Cluster Communication    │                          │
│                                    ▼                          │
│  ┌─────────────────┐    ┌─────────────────┐                  │
│  │PostgreSQL Service│    │  Flask App Pods │                  │
│  │(postgres-service)│◄───┤  (Port 5000)    │                  │
│  │   (Port 5432)   │    └─────────────────┘                  │
│  └─────────────────┘              │                          │
│           │                       │                          │
│           ▼                       ▼                          │
│  ┌─────────────────┐    ┌─────────────────┐                  │
│  │  postgres-0     │    │ Redis Service   │                  │
│  │   (Port 5432)   │    │(redis-service)  │                  │
│  └─────────────────┘    │  (Port 6379)    │                  │
│                         └─────────────────┘                  │
│                                  │                           │
│                                  ▼                           │
│                         ┌─────────────────┐                  │
│                         │   Redis Pod     │                  │
│                         │  (Port 6379)    │                  │
│                         └─────────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
```

## Storage Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       STORAGE LAYER                             │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │  postgres-0     │    │ Flask App Pods  │                    │
│  │     Pod         │    │                 │                    │
│  └─────────┬───────┘    └─────────┬───────┘                    │
│            │                      │                            │
│            ▼                      ▼                            │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │PostgreSQL PVC   │    │  Uploads PVC    │                    │
│  │   (5Gi, RWO)    │    │   (2Gi, RWX)    │                    │
│  └─────────┬───────┘    └─────────┬───────┘                    │
│            │                      │                            │
│            ▼                      ▼                            │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │PostgreSQL PV    │    │  Uploads PV     │                    │
│  │   (5Gi, RWO)    │    │   (2Gi, RWX)    │                    │
│  │  hostPath       │    │   hostPath      │                    │
│  └─────────┬───────┘    └─────────┬───────┘                    │
│            │                      │                            │
│            ▼                      ▼                            │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │ /data/postgres  │    │ /data/uploads   │                    │
│  │  (Host Path)    │    │  (Host Path)    │                    │
│  └─────────────────┘    └─────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
```

## Configuration Management

```
┌─────────────────────────────────────────────────────────────────┐
│                   CONFIGURATION LAYER                           │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │   ConfigMap     │    │     Secret      │                    │
│  │                 │    │                 │                    │
│  │ • FLASK_ENV     │    │ • postgres-     │                    │
│  │ • UPLOAD_FOLDER │    │   password      │                    │
│  │ • POSTGRES_DB   │    │ • secret-key    │                    │
│  │ • POSTGRES_USER │    │ • database-url  │                    │
│  │ • REDIS_URL     │    │                 │                    │
│  └─────────┬───────┘    └─────────┬───────┘                    │
│            │                      │                            │
│            └──────────┬───────────┘                            │
│                       │                                        │
│                       ▼                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              ENVIRONMENT VARIABLES                      │   │
│  │                                                         │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │   │
│  │  │ Flask App   │  │ Flask App   │  │ postgres-0  │     │   │
│  │  │   Pod 1     │  │   Pod 2     │  │    Pod      │     │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘     │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Deployment Sequence

```
1. Namespace Creation
   └── finance-app namespace

2. Configuration Setup
   ├── ConfigMap (non-sensitive config)
   └── Secret (passwords, keys)

3. Storage Provisioning
   ├── PostgreSQL PV (5Gi)
   └── Uploads PV (2Gi)

4. Database Deployment
   ├── PostgreSQL Service (Headless)
   ├── PostgreSQL StatefulSet
   └── Automatic PVC creation

5. Cache Deployment
   ├── Redis Service
   └── Redis Deployment

6. Application Deployment
   ├── Init Container (wait for DB)
   ├── Flask App Deployment (2 replicas)
   └── Uploads PVC creation

7. External Access
   └── NodePort Services
```

## Resource Specifications

| Component | Type | Replicas | CPU Request | Memory Request | CPU Limit | Memory Limit |
|-----------|------|----------|-------------|----------------|-----------|--------------|
| Flask App | Deployment | 2 | 250m | 256Mi | 500m | 512Mi |
| PostgreSQL | StatefulSet | 1 | 250m | 256Mi | 500m | 512Mi |
| Redis | Deployment | 1 | 100m | 128Mi | 200m | 256Mi |

## Port Mapping

| Service | Internal Port | External Port | Protocol |
|---------|---------------|---------------|----------|
| Flask App | 5000 | 30080 (NodePort) | HTTP |
| PostgreSQL | 5432 | 30432 (NodePort) | TCP |
| Redis | 6379 | - (Internal only) | TCP |

## Health Checks

### Flask Application
- **Liveness Probe**: HTTP GET /health (60s initial, 30s period)
- **Readiness Probe**: HTTP GET /health (30s initial, 10s period)

### PostgreSQL
- **Liveness Probe**: pg_isready command (30s initial, 10s period)
- **Readiness Probe**: pg_isready command (5s initial, 5s period)

### Redis
- **Liveness Probe**: redis-cli ping (30s initial, 10s period)
- **Readiness Probe**: redis-cli ping (5s initial, 5s period)

## Access URLs

- **Application**: `http://<minikube-ip>:30080`
- **Database** (debug): `<minikube-ip>:30432`
- **Get Minikube IP**: `minikube ip`
- **Service URL**: `minikube service finance-app-nodeport -n finance-app`
