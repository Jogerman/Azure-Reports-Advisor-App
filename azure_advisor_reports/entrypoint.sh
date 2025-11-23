#!/bin/bash
set -e

echo "==================================="
echo "Starting Azure Advisor Backend"
echo "==================================="

# Wait for database to be ready
echo "Waiting for database..."
python << END
import sys
import time
import psycopg2
from decouple import config

max_attempts = 30
attempt = 0

while attempt < max_attempts:
    try:
        conn = psycopg2.connect(
            dbname=config('DB_NAME'),
            user=config('DB_USER'),
            password=config('DB_PASSWORD'),
            host=config('DB_HOST'),
            port=config('DB_PORT', default='5432')
        )
        conn.close()
        print("Database is ready!")
        sys.exit(0)
    except psycopg2.OperationalError:
        attempt += 1
        print(f"Database not ready, attempt {attempt}/{max_attempts}...")
        time.sleep(2)

print("Database connection failed after maximum attempts")
sys.exit(1)
END

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "==================================="
echo "Starting Gunicorn server..."
echo "==================================="

# Start Gunicorn
exec gunicorn azure_advisor_reports.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
