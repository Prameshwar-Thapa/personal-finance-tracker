#!/bin/bash

echo "🚀 Deploying Personal Finance Tracker..."

# Create network
docker network create finance-network 2>/dev/null || echo "Network already exists"

# Stop and remove existing containers
docker stop finance_postgres finance_redis finance_web 2>/dev/null || true
docker rm finance_postgres finance_redis finance_web 2>/dev/null || true

# Start PostgreSQL
echo "📊 Starting PostgreSQL..."
docker run -d \
  --name finance_postgres \
  --network finance-network \
  -e POSTGRES_DB=financedb \
  -e POSTGRES_USER=financeuser \
  -e POSTGRES_PASSWORD=financepass \
  -p 5433:5432 \
  --restart unless-stopped \
  postgres:13

# Start Redis
echo "🔴 Starting Redis..."
docker run -d \
  --name finance_redis \
  --network finance-network \
  -p 6379:6379 \
  --restart unless-stopped \
  redis:7-alpine

# Wait for databases
echo "⏳ Waiting for databases to start..."
sleep 10

# Start Flask app
echo "🌐 Starting Flask application..."
docker run -d \
  --name finance_web \
  --network finance-network \
  -e DATABASE_URL=postgresql://financeuser:financepass@finance_postgres:5432/financedb \
  -e SECRET_KEY=your-secret-key-change-in-production \
  -e FLASK_ENV=production \
  -e REDIS_URL=redis://finance_redis:6379/0 \
  -p 5000:5000 \
  --restart unless-stopped \
  prameshwar884/personal-finance-tracker-web:latest

echo "✅ Deployment complete!"
echo "🌐 Access your app at: http://localhost:5000"
echo ""
echo "📊 Check status:"
echo "  docker ps"
echo ""
echo "📝 View logs:"
echo "  docker logs finance_web -f"
