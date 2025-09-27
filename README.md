# Personal Finance Tracker 💰

*A full-stack web application I built to demonstrate modern cloud-native development and DevOps practices*

Hi! I'm Prameshwar, and this is my personal finance tracker application. I built this project to showcase my skills in full-stack development, containerization, Kubernetes orchestration, and CI/CD practices. It's not just a simple web app - it's a production-ready system that demonstrates real-world software engineering practices.

## 🎯 What This Project Demonstrates

Through this application, I've implemented:
- **Full-Stack Development**: Flask backend with responsive frontend
- **Cloud-Native Architecture**: Containerized microservices approach  
- **DevOps Practices**: Complete CI/CD pipeline with GitOps
- **Kubernetes Orchestration**: Production-ready container deployment
- **Database Management**: PostgreSQL with proper migrations
- **Security Best Practices**: Secrets management and authentication
- **Monitoring & Observability**: Prometheus and Grafana integration

## 🚀 Features

- **User Authentication**: Secure registration and login system
- **Transaction Management**: Add, view, and categorize income/expenses
- **Receipt Upload**: Store receipt images with file management
- **Dashboard Analytics**: Monthly summaries and spending insights
- **Category Management**: Organize transactions with custom categories
- **RESTful API**: JSON endpoints for mobile/external integrations
- **Responsive Design**: Mobile-friendly interface

## 🏗️ My Technical Stack

### Application Components
- **Backend**: Flask (Python) - chose for rapid development and flexibility
- **Database**: PostgreSQL with SQLAlchemy ORM - production-grade reliability
- **Frontend**: HTML5, CSS3, JavaScript - clean, responsive design
- **File Storage**: Local filesystem (designed to easily migrate to S3)
- **Caching**: Redis for session management
- **WSGI Server**: Gunicorn for production deployment

### Kubernetes Architecture I Implemented
- **Persistent Volumes**: For database and file storage
- **StatefulSets**: PostgreSQL database with persistent storage
- **Deployments**: Application pods with rolling updates
- **Services**: Load balancing and service discovery
- **ConfigMaps & Secrets**: Secure configuration management
- **Ingress**: HTTP/HTTPS routing with SSL termination

## 📋 Prerequisites

- Python 3.9+
- PostgreSQL 13+
- Docker & Docker Compose
- Kubernetes cluster (minikube, kind, or cloud provider)
- kubectl CLI tool

## 🛠️ Local Development Setup

### 1. Clone and Setup Environment

```bash
git clone <your-repo-url>
cd personal-finance-tracker

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your configuration
```

### 2. Database Setup

```bash
# Install PostgreSQL locally or use Docker
docker run --name postgres-dev -e POSTGRES_PASSWORD=password -p 5432:5432 -d postgres:13

# Create database
createdb financedb

# Initialize database tables
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 3. Run Application Locally

```bash
# Method 1: Direct Python execution
python run.py

# Method 2: Flask development server
export FLASK_APP=run.py
export FLASK_ENV=development
flask run --host=0.0.0.0 --port=5000

# Access application at: http://localhost:5000
```

### 4. Test the Application

```bash
# Create test user account
# Navigate to http://localhost:5000/register

# Add sample transactions
# Upload receipt images
# Test API endpoints: http://localhost:5000/api/transactions
```

## 🐳 Docker Development

### Build and Run with Docker Compose

```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f web

# Stop services
docker-compose down

# Clean up volumes (WARNING: This deletes data)
docker-compose down -v
```

### Individual Docker Commands

```bash
# Build application image
docker build -t finance-tracker:latest .

# Run with external PostgreSQL
docker run -d \
  --name finance-app \
  -p 5000:5000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  -e SECRET_KEY=your-secret-key \
  finance-tracker:latest
```

## ☸️ Kubernetes Deployment

### Prerequisites Setup

```bash
# Start minikube (for local testing)
minikube start --driver=docker --memory=4096 --cpus=2

# Enable ingress addon
minikube addons enable ingress

# Verify cluster
kubectl cluster-info
```

### Deploy to Kubernetes

```bash
# Create namespace and deploy all components
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n finance-tracker
kubectl get services -n finance-tracker
kubectl get pvc -n finance-tracker

# Get application URL (minikube)
minikube service finance-app-service -n finance-tracker --url

# Port forward for testing
kubectl port-forward -n finance-tracker service/finance-app-service 8080:80
```

### Kubernetes Components

```bash
# View all resources
kubectl get all -n finance-tracker

# Check persistent volumes
kubectl get pv
kubectl get pvc -n finance-tracker

# View logs
kubectl logs -f deployment/finance-app -n finance-tracker

# Scale application
kubectl scale deployment finance-app --replicas=3 -n finance-tracker
```

## 🛠️ Development Scripts

The project includes several utility scripts for development and testing:

### **Sample Data Population**
```bash
# Populate database with realistic sample data
python scripts/populate_sample_data.py
```

### **Setup Validation**
```bash
# Validate Flask configuration and file structure
python scripts/validate_setup.py
```

### **Performance Benchmarking**
```bash
# Run database and application performance tests
python scripts/performance_benchmark.py
```

## 🧪 Testing

### Run Tests Locally

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run unit tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=html
```

### API Testing

```bash
# Health check
curl http://localhost:5000/health

# Get transactions (requires authentication)
curl -X GET http://localhost:5000/api/transactions \
  -H "Content-Type: application/json"

# Test file upload
curl -X POST http://localhost:5000/add_transaction \
  -F "amount=25.50" \
  -F "description=Lunch" \
  -F "transaction_type=expense" \
  -F "receipt=@receipt.jpg"
```

## 📊 Monitoring and Observability

### Application Metrics

```bash
# Check application health
kubectl get pods -n finance-tracker
kubectl describe pod <pod-name> -n finance-tracker

# View resource usage
kubectl top pods -n finance-tracker
kubectl top nodes
```

### Database Monitoring

```bash
# Connect to PostgreSQL pod
kubectl exec -it postgres-0 -n finance-tracker -- psql -U financeuser -d financedb

# Check database size
SELECT pg_size_pretty(pg_database_size('financedb'));

# View active connections
SELECT count(*) FROM pg_stat_activity;
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `sqlite:///finance.db` |
| `SECRET_KEY` | Flask secret key | `dev-secret-key` |
| `UPLOAD_FOLDER` | File upload directory | `static/uploads/receipts` |
| `MAX_CONTENT_LENGTH` | Max file upload size | `16MB` |

### Kubernetes ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: finance-app-config
data:
  DATABASE_URL: "postgresql://user:pass@postgres:5432/financedb"
  UPLOAD_FOLDER: "/app/static/uploads/receipts"
```

## 🚀 Production Deployment

### Security Considerations

1. **Secrets Management**: Use Kubernetes secrets for sensitive data
2. **HTTPS**: Configure TLS certificates with cert-manager
3. **Database Security**: Enable SSL, use strong passwords
4. **File Uploads**: Implement virus scanning, size limits
5. **Authentication**: Add rate limiting, CAPTCHA

### Scaling Strategies

```bash
# Horizontal Pod Autoscaler
kubectl autoscale deployment finance-app --cpu-percent=70 --min=2 --max=10 -n finance-tracker

# Vertical scaling
kubectl patch deployment finance-app -n finance-tracker -p '{"spec":{"template":{"spec":{"containers":[{"name":"finance-app","resources":{"requests":{"memory":"512Mi","cpu":"500m"}}}]}}}}'
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Troubleshooting

### Common Issues

**Database Connection Issues**
```bash
# Check PostgreSQL pod status
kubectl get pods -n finance-tracker | grep postgres

# View PostgreSQL logs
kubectl logs postgres-0 -n finance-tracker
```

**File Upload Issues**
```bash
# Check PVC status
kubectl get pvc -n finance-tracker

# Verify mount points
kubectl exec deployment/finance-app -n finance-tracker -- df -h
```

**Application Not Starting**
```bash
# Check application logs
kubectl logs deployment/finance-app -n finance-tracker

# Describe pod for events
kubectl describe pod <pod-name> -n finance-tracker
```

## 📞 Support

For questions and support:
- Create an issue in the GitHub repository
- Check the troubleshooting section above
- Review Kubernetes documentation for cluster-specific issues

---

**Built with ❤️ for learning Kubernetes and modern application development**
