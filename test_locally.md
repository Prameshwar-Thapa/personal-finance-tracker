# Testing Personal Finance Tracker Locally (Without Docker)

This guide will help you set up and test the Personal Finance Tracker application on your local machine without using Docker.

## 📋 Prerequisites

### System Requirements
- **Python 3.9+** (Check with: `python --version` or `python3 --version`)
- **SQLite** (comes with Python - no separate installation needed)
- **Git** (for version control)
- **Virtual environment support** (venv - comes with Python)

### Install System Dependencies

#### On Ubuntu/Debian:
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

#### On macOS:
```bash
# Python 3 usually comes pre-installed, but you can install via Homebrew if needed
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python (if needed)
brew install python
```

#### On Windows:
1. Download and install Python from [python.org](https://python.org) (make sure to check "Add Python to PATH")
2. Install Git from [git-scm.com](https://git-scm.com)

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

# Install all required packages (including email-validator)
pip install -r requirements.txt

# If you get an email-validator error, install it separately:
pip install email-validator

# Verify installation
pip list | grep -E "(Flask|email|wtforms)"
```

### Step 4: Setup Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# The .env file is already configured for SQLite by default
# DATABASE_URL=sqlite:///finance.db
```

### Step 5: Create Required Directories
```bash
# Create upload directories
mkdir -p static/uploads/receipts
mkdir -p static/css
mkdir -p static/js

# Set proper permissions (Linux/macOS)
chmod 755 static/uploads/receipts
```

### Step 6: Set Environment Variables
```bash
# Set Flask environment variables
export FLASK_APP=run.py
export FLASK_ENV=development

# On Windows use:
# set FLASK_APP=run.py
# set FLASK_ENV=development
```

### Step 7: Run the Application
```bash
# Direct Python execution (Recommended)
python run.py

# Alternative: Using Flask command
flask run --host=0.0.0.0 --port=5000
```

### Expected Output
When you run `python run.py`, you should see:
```
Database tables created successfully!
Starting Personal Finance Tracker...
Access the application at: http://localhost:5000
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

## 🧪 Testing the Application

### Step 1: Access the Application
Open your web browser and navigate to:
```
http://localhost:5000
```

You should see the Personal Finance Tracker homepage with options to Register or Login.

### Step 2: Create Test User Account
1. Click on "Register" in the navigation bar
2. Fill in the registration form:
   - **Username**: `testuser`
   - **Email**: `test@example.com`
   - **Password**: `testpass123`
   - **Confirm Password**: `testpass123`
3. Click "Register"
4. You should see a success message and be redirected to login

### Step 3: Login and Explore Dashboard
1. Login with your test credentials:
   - Username: `testuser`
   - Password: `testpass123`
2. You should see the dashboard with:
   - Welcome message
   - Financial summary cards (all showing $0.00 initially)
   - Default categories created automatically
   - Empty recent transactions section

### Step 4: Test Core Functionality

#### Add Sample Income Transaction
1. Click "Add Transaction" in the navigation
2. Fill in the form:
   - **Amount**: `2500.00`
   - **Description**: `Monthly Salary`
   - **Type**: Select `Income`
   - **Category**: Select `Salary`
   - **Date**: Use current date (default)
   - **Notes**: `January salary payment`
3. Click "Add Transaction"
4. You should be redirected to the transactions page

#### Add Sample Expense Transaction
1. Click "Add Transaction" again
2. Fill in the form:
   - **Amount**: `45.50`
   - **Description**: `Grocery Shopping`
   - **Type**: Select `Expense`
   - **Category**: Select `Food & Dining`
   - **Date**: Use current date
   - **Receipt**: Upload a test image (JPG/PNG) if available
   - **Notes**: `Weekly groceries`
3. Click "Add Transaction"

#### Add More Test Transactions
Add a few more transactions to see the dashboard populate:
- Coffee: $5.50 (Expense, Food & Dining)
- Gas: $40.00 (Expense, Transportation)
- Freelance: $300.00 (Income, Other)

### Step 5: Test Dashboard Features
1. Navigate back to "Dashboard"
2. Verify the financial summary shows:
   - **Monthly Income**: Should show your income transactions
   - **Monthly Expenses**: Should show your expense transactions
   - **Monthly Balance**: Should show income minus expenses
   - **Total Balance**: Should show overall balance
3. Check that recent transactions appear in the list
4. Verify category breakdown shows expenses by category

### Step 6: Test Transactions Page
1. Click "Transactions" in the navigation
2. Verify all your transactions are listed
3. Check that:
   - Dates are displayed correctly
   - Categories show with color indicators
   - Income shows in green, expenses in red
   - Receipt icons appear for transactions with uploads

### Step 7: Test File Upload (Optional)
1. Create a small test image file (or use any JPG/PNG)
2. Add a new transaction with receipt upload
3. Verify the file is saved by checking:
   ```bash
   ls -la static/uploads/receipts/
   ```
4. You should see your uploaded file with a unique name

### Step 8: Test API Endpoints
```bash
# Test health check (should work without login)
curl http://localhost:5000/health

# Expected response:
# {"status":"healthy","timestamp":"2024-XX-XXTXX:XX:XX.XXXXXX","version":"1.0.0"}
```

## 🔍 SQLite Database Testing

### Step 1: Verify Database Creation
```bash
# Check if database file was created
ls -la finance.db

# Should show a file with size > 0 bytes
```

### Step 2: Inspect Database Directly
```bash
# Install SQLite command-line tool (if not already installed)
# Ubuntu/Debian:
sudo apt install sqlite3

# macOS (usually pre-installed):
# brew install sqlite3

# Access the database
sqlite3 finance.db
```

### Step 3: Run Database Queries
In the SQLite prompt, run these commands:
```sql
-- List all tables
.tables

-- Expected output: categories  transactions  users

-- View table structures
.schema users
.schema transactions
.schema categories

-- Check your user account
SELECT id, username, email, created_at FROM users;

-- Check default categories
SELECT id, name, color, user_id FROM categories;

-- Check your transactions
SELECT 
    t.id,
    t.description,
    t.amount,
    t.transaction_type,
    t.date,
    c.name as category_name
FROM transactions t
LEFT JOIN categories c ON t.category_id = c.id
ORDER BY t.created_at DESC;

-- Get financial summary
SELECT 
    transaction_type,
    COUNT(*) as count,
    SUM(amount) as total
FROM transactions 
GROUP BY transaction_type;

-- Exit SQLite
.quit
```

### Step 4: Test Database Persistence
```bash
# Stop the application (Ctrl+C in the terminal running the app)

# Restart the application
python run.py

# Login again - your data should still be there
# Navigate to dashboard - transactions should persist
```

### Step 5: Populate Test Data (Optional)
```bash
# Run the test data script to add sample transactions
python test_sqlite_data.py

# This will create:
# - Sample income and expense transactions
# - Various categories with transactions
# - Realistic financial data for testing
```

## 🔧 Verification Checklist

### ✅ Application Startup
- [ ] Application starts without errors
- [ ] No import errors in console
- [ ] Database file `finance.db` is created
- [ ] Static files and directories exist
- [ ] Application accessible at http://localhost:5000

### ✅ User Authentication
- [ ] User registration form works
- [ ] User can register successfully
- [ ] User can login with correct credentials
- [ ] User cannot login with wrong credentials
- [ ] User can logout successfully
- [ ] Session management works (stays logged in on refresh)

### ✅ Core Features
- [ ] Dashboard displays correctly after login
- [ ] Default categories are created automatically
- [ ] Add transaction form loads and works
- [ ] Income transactions can be added
- [ ] Expense transactions can be added
- [ ] Transactions appear in dashboard
- [ ] Transactions list page works
- [ ] Financial summaries calculate correctly

### ✅ Database Operations
- [ ] User data persists after application restart
- [ ] Transactions are saved correctly
- [ ] Categories are linked to transactions
- [ ] Data relationships work (user → transactions → categories)
- [ ] SQLite queries return expected results

### ✅ File System
- [ ] Upload directory exists (`static/uploads/receipts/`)
- [ ] File uploads work (if tested)
- [ ] Files are saved with unique names
- [ ] File permissions are correct

### ✅ API Endpoints
- [ ] Health check endpoint responds: `curl http://localhost:5000/health`
- [ ] Returns JSON with status "healthy"
- [ ] Application logs show no errors

## 🐛 Troubleshooting

### Common Issues and Solutions

#### Issue: "ModuleNotFoundError: No module named 'email_validator'"
```bash
# Solution: Install the missing package
pip install email-validator

# Or reinstall all requirements
pip install -r requirements.txt
```

#### Issue: "Permission denied" for uploads directory
```bash
# Fix upload directory permissions
mkdir -p static/uploads/receipts
chmod -R 755 static/uploads/
```

#### Issue: "Port already in use" (Address already in use)
```bash
# Find process using port 5000
lsof -i :5000

# Kill the process (replace PID with actual process ID)
kill -9 <PID>

# Or use a different port
python run.py  # Edit run.py to use port 5001
```

#### Issue: "Template not found"
```bash
# Verify all template files exist
ls -la templates/
# Should contain: base.html, dashboard.html, index.html, login.html, register.html, add_transaction.html, transactions.html
```

#### Issue: "Static files not loading" (CSS/JS not working)
```bash
# Check static directory structure
ls -la static/
# Should contain: css/, js/, uploads/

# Verify CSS and JS files exist
ls -la static/css/style.css
ls -la static/js/main.js
```

#### Issue: Database errors or "no such table"
```bash
# Delete database and restart (WARNING: This deletes all data)
rm finance.db
python run.py

# The database will be recreated automatically
```

#### Issue: Virtual environment not activated
```bash
# Make sure you see (venv) in your prompt
# If not, activate it:
source venv/bin/activate

# Verify Python path
which python
# Should point to: /path/to/your/project/venv/bin/python
```

## 📊 Performance Testing

### Basic Load Testing
```bash
# Test multiple requests to the homepage
for i in {1..10}; do
  curl -s -o /dev/null -w "%{http_code} - %{time_total}s\n" http://localhost:5000/
done

# Expected: All requests should return 200 status
```

### Memory Usage Monitoring
```bash
# Monitor Python process memory usage
ps aux | grep python | grep run.py

# Monitor with top (press 'q' to quit)
top -p $(pgrep -f "python run.py")
```

### Database Performance
```bash
# Check database file size growth
ls -lh finance.db

# Run performance test script (if created)
python test_sqlite_performance.py
```

## 🚀 Next Steps After Successful Local Testing

Once your local testing is complete and successful:

### 1. Document Your Results
```bash
# Create a test results log
echo "# Local Testing Results - $(date)" > test_results.md
echo "✅ Application startup: SUCCESS" >> test_results.md
echo "✅ User registration: SUCCESS" >> test_results.md
echo "✅ Transaction creation: SUCCESS" >> test_results.md
echo "✅ Database persistence: SUCCESS" >> test_results.md
echo "✅ File uploads: SUCCESS" >> test_results.md
```

### 2. Prepare for Docker Testing
```bash
# Test with Docker Compose
docker-compose up --build

# This will test the same application in containers
```

### 3. Prepare for Kubernetes Deployment
```bash
# Create Kubernetes manifests (covered in separate guide)
# Deploy to local Kubernetes cluster (minikube/kind)
```

### 4. Portfolio Documentation
- Take screenshots of the working application
- Document the features you implemented
- Note any customizations or improvements you made
- Prepare talking points for interviews

## 🎯 Success Criteria

Your local setup is successful when:
- ✅ Application starts without errors
- ✅ You can register and login users
- ✅ Transactions can be created and viewed
- ✅ Dashboard displays financial summaries correctly
- ✅ Database persists data between restarts
- ✅ File uploads work (if tested)
- ✅ API endpoints respond correctly
- ✅ No error messages in console or browser

## 📝 Test Data for Resume/Portfolio

After successful testing, you can mention:
- **Built a personal finance tracker** with user authentication
- **Implemented SQLite database** with proper relationships
- **Created responsive web interface** with Bootstrap
- **Handled file uploads** for receipt management
- **Developed RESTful API endpoints** for data access
- **Used Flask framework** with proper MVC architecture
- **Implemented form validation** and security measures

---

**Congratulations! 🎉**

Once you've successfully completed local testing, you're ready to move on to:
1. **Docker containerization** (`docker-compose up`)
2. **Kubernetes deployment** (using the k8s manifests)
3. **Cloud deployment** (AWS, GCP, or Azure)

This local testing experience gives you hands-on knowledge of:
- Python web development
- Database design and operations
- File handling and uploads
- User authentication and sessions
- API development
- Debugging and troubleshooting

Perfect foundation for your AWS Cloud Engineer portfolio! 🚀
