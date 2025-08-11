#!/usr/bin/env python3
"""
Sample Data Population Script for Personal Finance Tracker

This script populates the application database with realistic sample data
for demonstration and testing purposes. It creates:
- A test user account
- Default expense/income categories  
- Sample transactions across different categories
- Realistic financial data for portfolio demonstration

Usage:
    python populate_sample_data.py

Requirements:
    - Application database must be initialized
    - Virtual environment must be activated
"""

import sys
import os
from datetime import datetime, date, timedelta
import random

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Transaction, Category

def create_test_data():
    """Create test data for the finance tracker"""
    
    app = create_app()
    
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        print("Creating test user...")
        
        # Create test user
        test_user = User.query.filter_by(username='testuser').first()
        if not test_user:
            test_user = User(username='testuser', email='test@example.com')
            test_user.set_password('testpass123')
            db.session.add(test_user)
            db.session.commit()
            print("✅ Test user created")
        else:
            print("✅ Test user already exists")
        
        # Check if categories exist, if not create default ones
        categories = Category.query.filter_by(user_id=test_user.id).all()
        if not categories:
            print("Creating default categories...")
            default_categories = [
                ('Food & Dining', '#ff6b6b'),
                ('Transportation', '#4ecdc4'),
                ('Shopping', '#45b7d1'),
                ('Entertainment', '#f9ca24'),
                ('Bills & Utilities', '#f0932b'),
                ('Healthcare', '#eb4d4b'),
                ('Salary', '#6c5ce7'),
                ('Other', '#a0a0a0')
            ]
            
            for cat_name, cat_color in default_categories:
                category = Category(name=cat_name, color=cat_color, user_id=test_user.id)
                db.session.add(category)
            
            db.session.commit()
            print("✅ Default categories created")
        
        # Get categories for transactions
        categories = Category.query.filter_by(user_id=test_user.id).all()
        category_dict = {cat.name: cat.id for cat in categories}
        
        # Create sample transactions
        print("Creating sample transactions...")
        
        sample_transactions = [
            # Income transactions
            (3000.00, 'Monthly Salary', 'income', 'Salary', date.today() - timedelta(days=30)),
            (500.00, 'Freelance Project', 'income', 'Other', date.today() - timedelta(days=15)),
            (200.00, 'Side Gig', 'income', 'Other', date.today() - timedelta(days=10)),
            
            # Expense transactions
            (450.00, 'Grocery Shopping', 'expense', 'Food & Dining', date.today() - timedelta(days=25)),
            (80.00, 'Gas Station', 'expense', 'Transportation', date.today() - timedelta(days=20)),
            (120.00, 'Electric Bill', 'expense', 'Bills & Utilities', date.today() - timedelta(days=18)),
            (45.50, 'Restaurant Dinner', 'expense', 'Food & Dining', date.today() - timedelta(days=12)),
            (25.00, 'Coffee Shop', 'expense', 'Food & Dining', date.today() - timedelta(days=8)),
            (150.00, 'Clothing Store', 'expense', 'Shopping', date.today() - timedelta(days=5)),
            (60.00, 'Movie Tickets', 'expense', 'Entertainment', date.today() - timedelta(days=3)),
            (35.00, 'Pharmacy', 'expense', 'Healthcare', date.today() - timedelta(days=1)),
        ]
        
        for amount, description, trans_type, category_name, trans_date in sample_transactions:
            # Check if transaction already exists
            existing = Transaction.query.filter_by(
                user_id=test_user.id,
                description=description,
                amount=amount
            ).first()
            
            if not existing:
                transaction = Transaction(
                    amount=amount,
                    description=description,
                    transaction_type=trans_type,
                    date=trans_date,
                    category_id=category_dict.get(category_name),
                    user_id=test_user.id
                )
                db.session.add(transaction)
        
        db.session.commit()
        print("✅ Sample transactions created")
        
        # Print summary
        print("\n📊 Database Summary:")
        print(f"Users: {User.query.count()}")
        print(f"Categories: {Category.query.count()}")
        print(f"Transactions: {Transaction.query.count()}")
        
        # Print user summary
        total_income = sum(t.amount for t in test_user.transactions if t.transaction_type == 'income')
        total_expenses = sum(t.amount for t in test_user.transactions if t.transaction_type == 'expense')
        balance = total_income - total_expenses
        
        print(f"\n💰 Test User Financial Summary:")
        print(f"Total Income: ${total_income:.2f}")
        print(f"Total Expenses: ${total_expenses:.2f}")
        print(f"Balance: ${balance:.2f}")
        
        print("\n✅ Test data creation completed!")
        print("You can now login with:")
        print("Username: testuser")
        print("Password: testpass123")

if __name__ == '__main__':
    create_test_data()
