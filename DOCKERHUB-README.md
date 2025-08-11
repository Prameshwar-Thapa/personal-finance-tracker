# Personal Finance Tracker

A full-stack web application for managing personal finances with transaction tracking, receipt uploads, and financial analytics.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Ports 5000, 5433, 6379 available

### Run with Docker Compose (Recommended)

1. **Create docker-compose.yml:**
```yaml
services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: financedb
      POSTGRES_USER: financeuser
      POSTGRES_PASSWORD: financepass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5433:5432"

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

  web:
    image: yourusername/personal-finance-tracker:latest
    environment:
      - DATABASE_URL=postgresql://financeuser:financepass@postgres:5432/financedb
      - SECRET_KEY=change-this-secret-key
      - FLASK_ENV=production
    volumes:
      - upload_data:/app/static/uploads
    ports:
      - "5000:5000"
    depends_on:
      - postgres
      - redis

volumes:
  postgres_data:
  redis_data:
  upload_data:
```

2. **Start the application:**
```bash
docker-compose up -d
```

3. **Initialize database:**
```bash
docker-compose exec web python -c "
from run import app, db
with app.app_context():
    db.create_all()
    print('Database ready!')
"
```

4. **Access the application:**
   - Open http://localhost:5000 in your browser
   - Register a new account
   - Start tracking your finances!

## 🔧 Manual Docker Run

If you prefer to run containers manually:

```bash
# Start PostgreSQL
docker run -d --name postgres \
  -e POSTGRES_DB=financedb \
  -e POSTGRES_USER=financeuser \
  -e POSTGRES_PASSWORD=financepass \
  -p 5433:5432 \
  postgres:13

# Start Redis
docker run -d --name redis \
  -p 6379:6379 \
  redis:7-alpine

# Start the web application
docker run -d --name finance-web \
  --link postgres:postgres \
  --link redis:redis \
  -e DATABASE_URL=postgresql://financeuser:financepass@postgres:5432/financedb \
  -e SECRET_KEY=your-secret-key \
  -p 5000:5000 \
  yourusername/personal-finance-tracker:latest
```

## ✨ Features

- 👤 User authentication and registration
- 💰 Income and expense tracking
- 📊 Financial dashboard with analytics
- 📎 Receipt upload and management
- 🏷️ Transaction categorization
- 📱 Responsive web interface
- 🔍 Transaction search and filtering
- ✏️ Edit and delete transactions

## 🧪 Health Check

```bash
# Check application health
curl http://localhost:5000/health

# Expected response:
# {"status":"healthy","timestamp":"...","version":"1.0.0"}
```

## 🛑 Stopping the Application

```bash
# Stop all services
docker-compose down

# Stop and remove all data
docker-compose down -v
```

## 📊 Monitoring

```bash
# View application logs
docker-compose logs -f web

# Monitor all containers
docker-compose ps

# Check resource usage
docker stats
```

## 🔧 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `SECRET_KEY` | Flask secret key | Required |
| `FLASK_ENV` | Flask environment | `production` |

## 🐛 Troubleshooting

### Port Conflicts
Change ports in docker-compose.yml if needed:
```yaml
ports:
  - "5001:5000"  # Use different port
```

### Database Issues
```bash
# Check database connection
docker-compose exec postgres pg_isready -U financeuser -d financedb

# View database logs
docker-compose logs postgres
```

### Permission Issues
```bash
# Fix upload permissions
docker-compose exec web chown -R appuser:appuser /app/static/uploads
```

## 📚 Documentation

- **GitHub Repository:** https://github.com/yourusername/personal-finance-tracker
- **Docker Hub:** https://hub.docker.com/r/yourusername/personal-finance-tracker

## 🏷️ Tags

- `latest` - Latest stable version
- `v1.0` - Version 1.0 release

## 📄 License

MIT License - see repository for details.

---

**Built with:** Flask, PostgreSQL, Redis, Docker
**Maintained by:** Your Name
