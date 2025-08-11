#!/bin/bash

# Fix permissions for upload directory
mkdir -p /app/static/uploads/receipts
chown -R appuser:appuser /app/static/uploads
chmod -R 755 /app/static/uploads

# Switch to appuser and start the application
exec runuser -u appuser -- gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 run:app
