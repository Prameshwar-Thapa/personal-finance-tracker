from app import create_app, db
import os

app = create_app()

# Create tables when the app starts (works with both Flask dev server and Gunicorn)
def init_database():
    """Initialize database tables safely"""
    try:
        with app.app_context():
            # Check if tables exist, if not create them
            db.create_all()
            print("Database tables initialized successfully!")
    except Exception as e:
        print(f"Database initialization error (may be normal if tables exist): {e}")

# Initialize database on import (works with Gunicorn)
init_database()

if __name__ == '__main__':
    print("Starting Personal Finance Tracker...")
    print("Access the application at: http://localhost:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
