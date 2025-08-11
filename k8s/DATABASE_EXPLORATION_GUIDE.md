# Database Pod Exploration Guide

## How to Access and Explore the PostgreSQL Database Pod

### Prerequisites
Make sure your application is deployed and running:
```bash
# Start Minikube
minikube start --memory=4096 --cpus=2

# Deploy the application
kubectl apply -f k8s/

# Verify PostgreSQL pod is running
kubectl get pods -n finance-app | grep postgres
```

## Method 1: Execute Shell in Database Pod

### Step 1: Find the PostgreSQL Pod
```bash
# List all pods in the finance-app namespace
kubectl get pods -n finance-app

# Get specifically the PostgreSQL pod
kubectl get pods -n finance-app | grep postgres
# Output should show: postgres-0
```

### Step 2: Access the Pod Shell
```bash
# Execute bash shell in the PostgreSQL pod
kubectl exec -it postgres-0 -n finance-app -- /bin/bash

# Alternative: Use sh if bash is not available
kubectl exec -it postgres-0 -n finance-app -- /bin/sh
```

### Step 3: Explore the Database Storage
Once inside the pod, you can explore the PostgreSQL data directory:

```bash
# Navigate to PostgreSQL data directory
cd /var/lib/postgresql/data

# List contents of the data directory
ls -la

# Check the PGDATA directory (where actual data is stored)
cd pgdata
ls -la

# View PostgreSQL configuration
cat postgresql.conf

# Check database files
ls -la base/
```

## Method 2: Connect to PostgreSQL Database

### Step 1: Access PostgreSQL CLI
```bash
# Connect to PostgreSQL from within the pod
kubectl exec -it postgres-0 -n finance-app -- psql -U financeuser -d financedb
```

### Step 2: Explore Database Structure
Once connected to PostgreSQL:

```sql
-- List all databases
\l

-- Connect to the finance database
\c financedb

-- List all tables
\dt

-- Describe table structure (if tables exist)
\d table_name

-- View table data
SELECT * FROM table_name LIMIT 10;

-- Check database size
SELECT pg_size_pretty(pg_database_size('financedb'));

-- List all schemas
\dn

-- Exit PostgreSQL
\q
```

## Method 3: Port Forward and Connect Externally

### Step 1: Port Forward PostgreSQL Service
```bash
# Forward PostgreSQL port to your local machine
kubectl port-forward svc/postgres-service 5432:5432 -n finance-app
```

### Step 2: Connect from Local Machine
```bash
# Connect using psql from your local machine (if installed)
psql -h localhost -U financeuser -d financedb -p 5432

# Or use the NodePort service (if available)
minikube ip  # Get the IP
# Then connect to <minikube-ip>:30432
```

## Method 4: Explore Persistent Volume Storage

### Step 1: Check Persistent Volume Claims
```bash
# List PVCs
kubectl get pvc -n finance-app

# Describe PostgreSQL PVC
kubectl describe pvc postgres-storage-postgres-0 -n finance-app
```

### Step 2: Check Persistent Volumes
```bash
# List PVs
kubectl get pv

# Describe PostgreSQL PV
kubectl describe pv postgres-pv
```

### Step 3: Access Host Storage (Minikube)
```bash
# SSH into Minikube node
minikube ssh

# Navigate to the host path where PostgreSQL data is stored
cd /data/postgres

# List contents
ls -la

# View PostgreSQL files on the host
sudo ls -la pgdata/
```

## Database File Structure Exploration

### Understanding PostgreSQL Directory Structure
```bash
# Inside the pod, explore these key directories:

# Main data directory
/var/lib/postgresql/data/pgdata/
├── base/           # Database files (one subdirectory per database)
├── global/         # Cluster-wide tables
├── pg_wal/         # Write-Ahead Logging files
├── pg_tblspc/      # Tablespaces
├── postgresql.conf # Main configuration file
├── pg_hba.conf     # Host-based authentication
└── postmaster.pid  # Process ID file

# Database-specific files (in base/ directory)
base/
├── 1/              # template1 database
├── 13395/          # template0 database  
├── 16384/          # Your financedb database (ID varies)
└── ...
```

### Exploring Database Files
```bash
# Inside the pod, check database files
cd /var/lib/postgresql/data/pgdata/base

# List databases with their OIDs
ls -la

# Find your database OID
# Connect to PostgreSQL and run:
# SELECT oid, datname FROM pg_database;

# Explore specific database files
cd 16384  # Replace with your database OID
ls -la

# These files contain your actual table data:
# - Files without extension: Table data
# - Files with _fsm extension: Free space maps
# - Files with _vm extension: Visibility maps
```

## Useful Commands for Database Exploration

### Check Database Status
```bash
# Inside the pod
kubectl exec -it postgres-0 -n finance-app -- pg_isready -U financeuser

# Check PostgreSQL version
kubectl exec -it postgres-0 -n finance-app -- psql -U financeuser -d financedb -c "SELECT version();"

# Check database connections
kubectl exec -it postgres-0 -n finance-app -- psql -U financeuser -d financedb -c "SELECT * FROM pg_stat_activity;"
```

### Monitor Database Performance
```bash
# Check database size
kubectl exec -it postgres-0 -n finance-app -- psql -U financeuser -d financedb -c "SELECT pg_size_pretty(pg_database_size('financedb'));"

# Check table sizes (if tables exist)
kubectl exec -it postgres-0 -n finance-app -- psql -U financeuser -d financedb -c "SELECT schemaname,tablename,pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size FROM pg_tables WHERE schemaname NOT IN ('information_schema', 'pg_catalog') ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

### Backup and Restore
```bash
# Create a database dump
kubectl exec -it postgres-0 -n finance-app -- pg_dump -U financeuser financedb > backup.sql

# Copy files from pod to local machine
kubectl cp finance-app/postgres-0:/tmp/backup.sql ./backup.sql

# Copy files from local machine to pod
kubectl cp ./backup.sql finance-app/postgres-0:/tmp/backup.sql
```

## Troubleshooting Database Issues

### Check Logs
```bash
# View PostgreSQL logs
kubectl logs postgres-0 -n finance-app

# Follow logs in real-time
kubectl logs -f postgres-0 -n finance-app

# Check previous container logs (if pod restarted)
kubectl logs postgres-0 -n finance-app --previous
```

### Check Configuration
```bash
# View current PostgreSQL configuration
kubectl exec -it postgres-0 -n finance-app -- psql -U financeuser -d financedb -c "SHOW ALL;"

# Check specific configuration parameters
kubectl exec -it postgres-0 -n finance-app -- psql -U financeuser -d financedb -c "SHOW shared_preload_libraries;"
kubectl exec -it postgres-0 -n finance-app -- psql -U financeuser -d financedb -c "SHOW max_connections;"
```

### Check Disk Usage
```bash
# Check disk usage inside the pod
kubectl exec -it postgres-0 -n finance-app -- df -h

# Check PostgreSQL data directory size
kubectl exec -it postgres-0 -n finance-app -- du -sh /var/lib/postgresql/data
```

## Security Considerations

### Environment Variables
```bash
# Check environment variables in the pod
kubectl exec -it postgres-0 -n finance-app -- env | grep POSTGRES

# View how secrets are mounted
kubectl exec -it postgres-0 -n finance-app -- ls -la /var/run/secrets/
```

### File Permissions
```bash
# Check file permissions in data directory
kubectl exec -it postgres-0 -n finance-app -- ls -la /var/lib/postgresql/data

# Check PostgreSQL process owner
kubectl exec -it postgres-0 -n finance-app -- ps aux | grep postgres
```

## Example Session

Here's a complete example of exploring the database:

```bash
# 1. Deploy the application
kubectl apply -f k8s/

# 2. Wait for PostgreSQL to be ready
kubectl wait --for=condition=ready pod/postgres-0 -n finance-app --timeout=300s

# 3. Access the pod
kubectl exec -it postgres-0 -n finance-app -- /bin/bash

# 4. Inside the pod - explore file system
cd /var/lib/postgresql/data
ls -la
cd pgdata
ls -la

# 5. Connect to database
psql -U financeuser -d financedb

# 6. Inside PostgreSQL - explore database
\l                          # List databases
\c financedb               # Connect to database
\dt                        # List tables
SELECT version();          # Check version
\q                         # Exit

# 7. Exit the pod
exit
```

This guide provides comprehensive methods to explore and understand how your PostgreSQL database is stored and managed within the Kubernetes pod.
