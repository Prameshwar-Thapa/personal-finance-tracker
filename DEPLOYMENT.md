# Personal Finance Tracker - Deployment Guide

## 🚀 Quick Deployment from Docker Hub

This guide shows how to run the Personal Finance Tracker application on any computer using Docker Hub.

### Prerequisites
- Docker and Docker Compose installed
- Internet connection to download images
- Ports 5000, 5433, 6379 available

### Step 1: Download Deployment Files

**Option A: Download docker-compose file directly**
```bash
# Create a new directory
mkdir personal-finance-tracker
cd personal-finance-tracker

# Download the docker-compose file
curl -O https://raw.githubusercontent.com/yourusername/personal-finance-tracker/main/docker-compose-hub.yml

# Rename for easier use
mv docker-compose-hub.yml docker-compose.yml
```

**Option B: Create docker-compose.yml manually**
```bash
# Create a new directory
mkdir personal-finance-tracker
cd personal-finance-tracker

# Create docker-compose.yml file (copy content from the file above)
nano docker-compose.yml
```

### Step 2: Start the Application
```bash
# Pull images and start all services
docker-compose up -d

# Check if all containers are running
docker-compose ps

# Expected output:
# NAME               STATUS                    PORTS
# finance_postgres   Up (healthy)             0.0.0.0:5433->5432/tcp
# finance_redis      Up (healthy)             0.0.0.0:6379->6379/tcp  
# finance_web        Up (healthy)             0.0.0.0:5000->5000/tcp
```

### Step 3: Initialize Database
```bash
# Initialize database tables
docker-compose exec web python -c "
from run import app, db
with app.app_context():
    db.create_all()
    print('Database initialized successfully!')
"
```

### Step 4: Access the Application
```bash
# Open in browser
http://localhost:5000

# Or test with curl
curl http://localhost:5000/health
```

### Step 5: Test the Application
```bash
# Run health checks
curl http://localhost:5000/health

# Test Redis
docker-compose exec redis redis-cli ping

# Test PostgreSQL
docker-compose exec postgres pg_isready -U financeuser -d financedb
```

## 🛑 Stopping the Application
```bash
# Stop all services
docker-compose down

# Stop and remove all data (⚠️ This deletes all data!)
docker-compose down -v
```

## 🔧 Troubleshooting

### Port Conflicts
If ports are already in use, modify the docker-compose.yml:
```yaml
ports:
  - "5001:5000"  # Change 5000 to 5001
  - "5434:5432"  # Change 5433 to 5434
```

### Permission Issues
```bash
# Fix upload directory permissions
docker-compose exec web chown -R appuser:appuser /app/static/uploads
```

### Database Connection Issues
```bash
# Check database logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres
```

## 📊 Monitoring
```bash
# View logs
docker-compose logs -f web

# Monitor resource usage
docker stats

# Check container health
docker-compose ps
```

## 🔄 Updates
```bash
# Pull latest image and restart
docker-compose pull
docker-compose up -d
```

---

**Docker Hub Image:** `yourusername/personal-finance-tracker:latest`
**GitHub Repository:** `https://github.com/yourusername/personal-finance-tracker`
