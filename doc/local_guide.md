# Personal Finance Tracker - Local Development Guide

*I chose this personal finance management application to learn cloud engineering concepts like containerization, persistent storage, and Kubernetes deployments. This guide will help you get it running locally to understand the infrastructure requirements!*

## 🚀 Quick Start (5 Minutes to Running!)

### What You'll Need
- Python 3.9+ (check with `python3 --version`)
- That's it! Everything else gets installed automatically

### Let's Get Started!
```bash
# 1. Navigate to the project (if you just downloaded it)
cd personal-finance-tracker

# 2. Create a virtual environment (keeps things clean)
python3 -m venv venv

# 3. Activate it (you'll see (venv) in your terminal)
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 4. Install everything we need
pip install -r requirements.txt

# 5. Create folders for file uploads
mkdir -p static/uploads/receipts static/css static/js

# 6. Start the app!
python run.py
```

** That's it! Open your browser and go to: http://localhost:5000**

You should see the Personal Finance Tracker homepage. Create an account and start exploring!

###  No Database Setup Required!
**Important**: You don't need to install or configure any database! Here's why:
- **SQLite comes with Python** - No separate installation needed
- **Database auto-creates** - The `finance.db` file appears automatically on first run
- **Tables auto-generate** - All database structure is created by the application
- **Zero configuration** - Just run the app and it works!

**Local vs Cloud Database:**
- **Local (SQLite)**: File-based, perfect for development, zero setup
- **Cloud (PostgreSQL/MySQL)**: Managed service, high availability, requires configuration

This demonstrates the **infrastructure difference** between local development and production cloud deployment!

### When You're Done
```bash
# Stop the app by pressing Ctrl+C in the terminal
# Then deactivate the virtual environment
deactivate
```

## Understanding the Application (Cloud Engineering Perspective)

### The Application Stack
I'm using this application to demonstrate cloud infrastructure concepts:

- **Backend**: Flask (Python) - Stateless application layer
- **Database**: SQLite (local) / PostgreSQL (production) - Persistent data storage
- **Frontend**: HTML5, CSS3, JavaScript - Static assets for CDN
- **File Storage**: Local filesystem (local) / S3 (cloud) - Object storage patterns
- **Authentication**: Session-based - Stateful vs stateless considerations

### Why This Application for Cloud Learning?
- **Persistent Storage**: Demonstrates database and file storage requirements
- **Stateful Data**: Shows challenges of data persistence in containers
- **Multi-tier Architecture**: Frontend, backend, database separation
- **File Uploads**: Object storage and volume mounting concepts
- **User Sessions**: State management in distributed systems

## 💡 How It Works (Infrastructure Perspective)

### The Architecture Flow
```
User Browser → Load Balancer → Application Pods → Database
                            → Object Storage (files)
```

### Local vs Cloud Infrastructure
**Local Setup:**
- Single server running everything
- SQLite file-based database
- Local file system storage
- No load balancing

**Cloud Setup (What I'm Learning):**
- Multiple application instances
- Managed database service
- Object storage (S3)
- Load balancers and auto-scaling

## 🔍 Exploring Infrastructure Requirements

### First Time Setup
1. **Create an Account**: Test user authentication flow
2. **Add Some Categories**: Understand data relationships
3. **Add Transactions**: See database operations
4. **Upload a Receipt**: Test file storage requirements
5. **Check the Dashboard**: Observe data aggregation

### Infrastructure Patterns to Observe
- **Database Connections**: How the app connects to data storage
- **File Handling**: Where uploaded files are stored
- **Session Management**: How user state is maintained
- **Resource Usage**: Memory and CPU patterns
- **Data Persistence**: What happens when you restart the app

## 🛠️ Troubleshooting (Infrastructure Issues)

### "Port 5000 is already in use"
```bash
# Find what's using the port (service discovery concept)
lsof -i :5000

# Kill the process (container restart simulation)
kill -9 <PID>

# Or use a different port (load balancer port mapping)
# Change: app.run(host='0.0.0.0', port=5001, debug=True)
```

### "Can't find module xyz"
```bash
# Make sure your virtual environment is activated (container isolation)
source venv/bin/activate

# Reinstall requirements (dependency management)
pip install -r requirements.txt
```

### "Permission denied" for uploads
```bash
# Make sure the upload directory exists (persistent volume setup)
mkdir -p static/uploads/receipts
chmod 755 static/uploads/receipts
```

### App won't stop with Ctrl+C
```bash
# Force kill it (pod termination)
ps aux | grep "python run.py"
kill -9 <PID>
```

## 📊 Understanding Data Persistence

### What Gets Stored (Persistent Volume Requirements)
- **Database**: User accounts, transactions, categories
- **Files**: Receipt images in organized folders
- **Sessions**: User authentication state
- **Logs**: Application and error logs

### Storage Patterns
```
personal-finance-tracker/
├── finance.db                     # Database file (needs persistent volume)
├── static/uploads/receipts/        # File uploads (needs object storage)
│   └── 1/                         # User-specific folders
├── venv/                          # Dependencies (ephemeral)
└── [application files]            # Code (ephemeral)
```

### Cloud Storage Mapping
- **Database**: RDS, Cloud SQL, or managed PostgreSQL
- **File Uploads**: S3, GCS, or Azure Blob Storage
- **Application Code**: Container images
- **Configuration**: ConfigMaps and Secrets


## 🎯 Cloud Engineering Learning Objectives

### Infrastructure Skills Demonstrated
- **Containerization**: Understanding application packaging
- **Persistent Storage**: Database and file storage requirements
- **Service Architecture**: Multi-tier application design
- **Resource Management**: CPU, memory, and storage planning
- **Configuration Management**: Environment-specific settings
- **Monitoring**: Health checks and performance metrics

### Kubernetes Concepts Applied
- **Persistent Volumes**: For database and file storage
- **StatefulSets**: For database deployment
- **Deployments**: For stateless application pods
- **Services**: For load balancing and service discovery
- **ConfigMaps**: For application configuration
- **Secrets**: For sensitive data management

### Cloud Platform Skills
- **AWS**: EKS, RDS, S3, ALB, CloudWatch
## 🚀 Next Steps (Cloud Deployment Journey)

### Containerization (Docker)
```bash
# Test containerized version
docker-compose up --build
```

**Learning Objectives:**
- Container networking
- Volume mounting
- Environment variables
- Multi-container orchestration

### Kubernetes Deployment
```bash
# Deploy to Kubernetes cluster
kubectl apply -f k8s/
```

**Infrastructure Components:**
- Persistent Volume Claims for data
- StatefulSet for PostgreSQL
- Deployment for application
- Service for load balancing
- Ingress for external access

### Cloud Platform Deployment
**AWS Architecture:**
- EKS cluster for container orchestration
- RDS for managed database
- S3 for file storage
- ALB for load balancing
- CloudWatch for monitoring

**Infrastructure as Code:**
- Terraform for resource provisioning
- Helm charts for Kubernetes deployments
- CI/CD pipelines for automated deployment

## 💭 My Cloud Engineering Journey

### Why I Chose This Application
I needed a real application to understand cloud infrastructure concepts:
- How persistent storage works in containers
- How to handle stateful applications in Kubernetes
- How to design for scalability and high availability
- How to implement proper monitoring and logging
- How to manage secrets and configuration

### Infrastructure Challenges I'm Learning
- **Data Persistence**: How to maintain data across container restarts
- **Scalability**: How to scale stateless vs stateful components
- **Storage Management**: Object storage vs block storage use cases
- **Service Discovery**: How services find and communicate with each other
- **Configuration Management**: How to handle environment-specific settings
- **Monitoring**: How to observe application and infrastructure health

### Cloud Engineering Skills Developed
- **Container Orchestration**: Kubernetes deployment and management
- **CI/CD Pipelines**: Automated deployment workflows
- **Monitoring & Logging**: Observability implementation
- **Security**: Secrets management and network policies
- **Cost Optimization**: Resource sizing and auto-scaling

## 🏆 Conclusion

This Personal Finance Tracker serves as my practical learning platform for cloud engineering concepts. It demonstrates real-world infrastructure challenges like persistent storage, container orchestration, and multi-tier application deployment.


*Using this application as a learning vehicle for cloud engineering concepts. This project represents my hands-on approach to understanding production infrastructure patterns and container orchestration.*
