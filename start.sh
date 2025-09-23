#!/bin/bash

# Wait for database to be ready
echo "Waiting for database..."
while ! pg_isready -h postgres -p 5432 -U financeuser; do
    echo "Database not ready, waiting..."
    sleep 2
done

echo "Database is ready!"

# Initialize database if needed
echo "Initializing database..."
python -c "
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print('Database tables created successfully!')
"

# Start the application
echo "Starting Flask application..."
exec gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 run:app
