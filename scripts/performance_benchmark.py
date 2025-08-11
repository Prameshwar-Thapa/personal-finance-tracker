#!/usr/bin/env python3
"""
Performance Benchmark Script for Personal Finance Tracker

This script performs comprehensive performance testing of the SQLite database
and application components. It measures:
- Database insert/query performance
- Bulk operation efficiency
- Memory usage patterns
- Response time analysis

Usage:
    python performance_benchmark.py

Metrics Tested:
- Bulk insert rates (transactions/second)
- Query response times
- Database file size efficiency
- Concurrent operation simulation
"""

import sys
import os
import time
import random
from datetime import datetime, date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Transaction, Category

def performance_test():
    """Test SQLite database performance"""
    
    app = create_app()
    
    with app.app_context():
        print("🚀 Starting SQLite Performance Test...")
        
        # Get test user
        test_user = User.query.filter_by(username='testuser').first()
        if not test_user:
            print("❌ Test user not found. Run test_sqlite_data.py first.")
            return
        
        categories = Category.query.filter_by(user_id=test_user.id).all()
        if not categories:
            print("❌ No categories found. Run test_sqlite_data.py first.")
            return
        
        # Test 1: Bulk Insert Performance
        print("\n📝 Test 1: Bulk Insert Performance")
        start_time = time.time()
        
        bulk_transactions = []
        for i in range(1000):
            transaction = Transaction(
                amount=round(random.uniform(10.0, 500.0), 2),
                description=f'Test Transaction {i}',
                transaction_type=random.choice(['income', 'expense']),
                date=date.today() - timedelta(days=random.randint(1, 365)),
                category_id=random.choice(categories).id,
                user_id=test_user.id
            )
            bulk_transactions.append(transaction)
        
        db.session.bulk_save_objects(bulk_transactions)
        db.session.commit()
        
        insert_time = time.time() - start_time
        print(f"✅ Inserted 1000 transactions in {insert_time:.2f} seconds")
        print(f"📊 Rate: {1000/insert_time:.2f} transactions/second")
        
        # Test 2: Query Performance
        print("\n🔍 Test 2: Query Performance")
        
        # Simple query
        start_time = time.time()
        transactions = Transaction.query.filter_by(user_id=test_user.id).all()
        simple_query_time = time.time() - start_time
        print(f"✅ Simple query ({len(transactions)} records): {simple_query_time:.4f} seconds")
        
        # Complex query with joins
        start_time = time.time()
        complex_query = db.session.query(Transaction, Category)\
            .join(Category)\
            .filter(Transaction.user_id == test_user.id)\
            .filter(Transaction.transaction_type == 'expense')\
            .order_by(Transaction.date.desc())\
            .limit(100).all()
        complex_query_time = time.time() - start_time
        print(f"✅ Complex query with join ({len(complex_query)} records): {complex_query_time:.4f} seconds")
        
        # Aggregation query
        start_time = time.time()
        monthly_summary = db.session.query(
            db.func.strftime('%Y-%m', Transaction.date).label('month'),
            db.func.sum(Transaction.amount).label('total')
        ).filter_by(user_id=test_user.id)\
         .group_by(db.func.strftime('%Y-%m', Transaction.date))\
         .all()
        aggregation_time = time.time() - start_time
        print(f"✅ Aggregation query ({len(monthly_summary)} months): {aggregation_time:.4f} seconds")
        
        # Test 3: Database Size
        print("\n💾 Test 3: Database Size Analysis")
        db_size = os.path.getsize('finance.db')
        print(f"📁 Database file size: {db_size / 1024:.2f} KB")
        print(f"📊 Average bytes per transaction: {db_size / len(transactions):.2f}")
        
        # Test 4: Concurrent Access Simulation
        print("\n🔄 Test 4: Concurrent Operations Simulation")
        start_time = time.time()
        
        for i in range(100):
            # Simulate read operation
            Transaction.query.filter_by(user_id=test_user.id).first()
            
            # Simulate write operation
            if i % 10 == 0:
                new_transaction = Transaction(
                    amount=25.0,
                    description=f'Concurrent Test {i}',
                    transaction_type='expense',
                    date=date.today(),
                    category_id=categories[0].id,
                    user_id=test_user.id
                )
                db.session.add(new_transaction)
                db.session.commit()
        
        concurrent_time = time.time() - start_time
        print(f"✅ 100 mixed operations completed in {concurrent_time:.2f} seconds")
        
        print("\n🎯 Performance Test Summary:")
        print(f"- Bulk insert rate: {1000/insert_time:.2f} transactions/second")
        print(f"- Simple query time: {simple_query_time*1000:.2f} ms")
        print(f"- Complex query time: {complex_query_time*1000:.2f} ms")
        print(f"- Database size: {db_size / 1024:.2f} KB")
        print(f"- Total transactions: {Transaction.query.count()}")

if __name__ == '__main__':
    performance_test()
