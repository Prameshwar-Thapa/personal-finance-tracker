# Testing Personal Finance Tracker Locally (Without Docker)

This guide will help you set up and test the Personal Finance Tracker application on your local machine without using Docker.

## 📋 Prerequisites

### System Requirements
- **Python 3.9+** (Check with: `python --version` or `python3 --version`)
- **PostgreSQL 13+** (or SQLite for quick testing)
- **Git** (for version control)
- **Virtual environment support** (venv or virtualenv)

### Install System Dependencies

#### On Ubuntu/Debian:
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv postgresql postgresql-contrib libpq-dev
```

#### On macOS:
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python postgresql
```

#### On Windows:
1. Download and install Python from [python.org](https://python.org)
2. Download and install PostgreSQL from [postgresql.org](https://postgresql.org)
3. Install Git from [git-scm.com](https://git-scm.com)

## 🚀 Step-by-Step Setup

### Step 1: Navigate to Project Directory
```bash
cd /home/prameshwar/Desktop/personal-finance-tracker
```

### Step 2: Create and Activate Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate

# Verify activation (you should see (venv) in your prompt)
which python  # Should point to venv/bin/python
```

### Step 3: Install Python Dependencies
```bash
# Upgrade pip first
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt

# Verify installation
pip list
```

### Step 4: Database Setup Options

#### Option A: Quick Testing with SQLite (Recommended for first test)
```bash
# Copy environment template
cp .env.example .env

# Edit .env file to use SQLite (default)
# The DATABASE_URL should be: sqlite:///finance.db
```

#### Option B: Full PostgreSQL Setup (Production-like)
```bash
# Start PostgreSQL service
# On Ubuntu/Debian:
sudo systemctl start postgresql
sudo systemctl enable postgresql

# On macOS:
brew services start postgresql

# Create database and user
sudo -u postgres psql

# In PostgreSQL prompt, run:
CREATE DATABASE financedb;
CREATE USER financeuser WITH PASSWORD 'financepass';
GRANT ALL PRIVILEGES ON DATABASE financedb TO financeuser;
\q

# Update .env file
cp .env.example .env
# Edit .env and set:
# DATABASE_URL=postgresql://financeuser:financepass@localhost:5432/financedb
```

### Step 5: Initialize Database
```bash
# Set Flask app environment variable
export FLASK_APP=run.py
export FLASK_ENV=development

# Initialize database migrations (if using PostgreSQL)
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# For SQLite, the database will be created automatically
```

### Step 6: Create Required Directories
```bash
# Create upload directories
mkdir -p static/uploads/receipts
mkdir -p static/css
mkdir -p static/js

# Set proper permissions
chmod 755 static/uploads/receipts
```

### Step 7: Run the Application
```bash
# Method 1: Using Flask development server
export FLASK_APP=run.py
export FLASK_ENV=development
flask run --host=0.0.0.0 --port=5000

# Method 2: Direct Python execution
python run.py

# Method 3: Using Gunicorn (production-like)
gunicorn --bind 0.0.0.0:5000 --workers 1 --timeout 120 run:app
```

## 🧪 Testing the Application

### Step 1: Access the Application
Open your web browser and navigate to:
```
http://localhost:5000
```

### Step 2: Create Test User Account
1. Click on "Register" in the navigation
2. Fill in the registration form:
   - Username: `testuser`
   - Email: `test@example.com`
   - Password: `testpass123`
   - Confirm Password: `testpass123`
3. Click "Register"

### Step 3: Login and Test Features
1. Login with your test credentials
2. You should see the dashboard with default categories created

### Step 4: Test Core Functionality

#### Add Sample Transactions
1. Click "Add Transaction"
2. Add an income transaction:
   - Amount: `2500.00`
   - Description: `Monthly Salary`
   - Type: `Income`
   - Category: `Salary`
   - Date: Current date
3. Add an expense transaction:
   - Amount: `45.50`
   - Description: `Grocery Shopping`
   - Type: `Expense`
   - Category: `Food & Dining`
   - Upload a test receipt image (optional)

#### Test File Upload
1. Create a test image file or use any small image
2. When adding a transaction, upload the image as a receipt
3. Verify the file is saved in `static/uploads/receipts/`

#### Test Dashboard
1. Navigate to Dashboard
2. Verify monthly summaries are calculated correctly
3. Check that recent transactions appear
4. Verify category breakdown is displayed

#### Test API Endpoints
```bash
# Test health check
curl http://localhost:5000/health

# Test transactions API (requires login session)
curl -X GET http://localhost:5000/api/transactions \
  -H "Content-Type: application/json" \
  -b cookies.txt
```

## 🔍 Verification Checklist

### ✅ Application Startup
- [ ] Application starts without errors
- [ ] No import errors in console
- [ ] Database connection successful
- [ ] Static files loading correctly

### ✅ User Authentication
- [ ] User registration works
- [ ] User login/logout works
- [ ] Session management working
- [ ] Password hashing functional

### ✅ Core Features
- [ ] Dashboard displays correctly
- [ ] Add transaction form works
- [ ] File upload functionality works
- [ ] Transaction list displays
- [ ] Categories are created and assigned

### ✅ Database Operations
- [ ] User data persists after restart
- [ ] Transactions are saved correctly
- [ ] File paths stored in database
- [ ] Data relationships working

### ✅ File System
- [ ] Upload directory exists
- [ ] Files are saved with correct names
- [ ] File permissions are correct
- [ ] Thumbnails created (if applicable)

## 🐛 Troubleshooting

### Common Issues and Solutions

#### Issue: "ModuleNotFoundError"
```bash
# Solution: Ensure virtual environment is activated and dependencies installed
source venv/bin/activate
pip install -r requirements.txt
```

#### Issue: "Database connection failed"
```bash
# For PostgreSQL: Check if service is running
sudo systemctl status postgresql

# Check database exists
sudo -u postgres psql -l | grep financedb

# For SQLite: Check file permissions
ls -la finance.db
```

#### Issue: "Permission denied" for uploads
```bash
# Fix upload directory permissions
chmod -R 755 static/uploads/
chown -R $USER:$USER static/uploads/
```

#### Issue: "Port already in use"
```bash
# Find process using port 5000
lsof -i :5000

# Kill the process (replace PID)
kill -9 <PID>

# Or use different port
flask run --port=5001
```

#### Issue: "Template not found"
```bash
# Verify template directory structure
ls -la templates/
# Should contain: base.html, dashboard.html, etc.
```

#### Issue: Static files not loading
```bash
# Check static directory structure
ls -la static/
# Should contain: css/, js/, uploads/

# Verify CSS and JS files exist
ls -la static/css/style.css
ls -la static/js/main.js
```

## 📊 Performance Testing

### Load Testing with curl
```bash
# Test multiple requests
for i in {1..10}; do
  curl -w "@curl-format.txt" -o /dev/null -s http://localhost:5000/
done

# Create curl-format.txt:
echo "     time_namelookup:  %{time_namelookup}\n
        time_connect:  %{time_connect}\n
     time_appconnect:  %{time_appconnect}\n
    time_pretransfer:  %{time_pretransfer}\n
       time_redirect:  %{time_redirect}\n
  time_starttransfer:  %{time_starttransfer}\n
                     ----------\n
          time_total:  %{time_total}\n" > curl-format.txt
```

### Memory Usage Monitoring
```bash
# Monitor Python process memory
ps aux | grep python

# Monitor with top
top -p $(pgrep -f "python run.py")
```

## 🔧 Development Mode Features

### Enable Debug Mode
```bash
# Set environment variables
export FLASK_ENV=development
export FLASK_DEBUG=1

# Run with auto-reload
flask run --reload
```

### Database Inspection
```bash
# For PostgreSQL
psql -U financeuser -d financedb -h localhost

# Common queries:
\dt                          # List tables
SELECT * FROM users;         # View users
SELECT * FROM transactions; # View transactions
SELECT * FROM categories;   # View categories
```

### Log Monitoring
```bash
# View application logs in real-time
tail -f app.log

# For more verbose logging, add to .env:
LOG_LEVEL=DEBUG
```

## 🚀 Next Steps

After successful local testing:

1. **Test with Docker**: Use `docker-compose up` to test containerized version
2. **Kubernetes Deployment**: Deploy to local Kubernetes cluster (minikube)
3. **Production Setup**: Configure for production environment
4. **Monitoring**: Add application monitoring and logging
5. **Security**: Implement additional security measures

## 📝 Test Results Documentation

Create a test log to document your results:

```bash
# Create test results file
touch test_results.md

# Document your findings:
echo "# Test Results - $(date)" >> test_results.md
echo "- Application startup: ✅ Success" >> test_results.md
echo "- User registration: ✅ Success" >> test_results.md
echo "- Transaction creation: ✅ Success" >> test_results.md
echo "- File upload: ✅ Success" >> test_results.md
```

## 🆘 Getting Help

If you encounter issues:

1. Check the troubleshooting section above
2. Review application logs for error messages
3. Verify all prerequisites are installed correctly
4. Ensure virtual environment is activated
5. Check file and directory permissions

## 🎯 Success Criteria

Your local setup is successful when:
- ✅ Application starts without errors
- ✅ You can register and login users
- ✅ Transactions can be created and viewed
- ✅ File uploads work correctly
- ✅ Dashboard displays financial summaries
- ✅ API endpoints respond correctly
- ✅ Database persists data between restarts

---

**Happy Testing! 🚀**

Once you've successfully tested locally, you'll be ready to move on to Docker containerization and Kubernetes deployment for your cloud engineering portfolio.
