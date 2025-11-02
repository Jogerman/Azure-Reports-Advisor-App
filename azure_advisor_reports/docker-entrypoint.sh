#!/bin/sh
set -e

echo "Starting Azure Advisor Reports Backend..."

# Wait for database to be ready
echo "Waiting for database connection..."
python << END
import sys
import time
import psycopg2
from decouple import config

max_retries = 30
retry_interval = 2

for i in range(max_retries):
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
    except psycopg2.OperationalError as e:
        if i < max_retries - 1:
            print(f"Database not ready yet, retrying in {retry_interval}s... ({i+1}/{max_retries})")
            time.sleep(retry_interval)
        else:
            print("Could not connect to database!")
            sys.exit(1)
END

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --no-input

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --no-input --clear

# Create cache table if needed
echo "Setting up cache table..."
python manage.py createcachetable || true

# Start Celery Worker in background
echo "Starting Celery worker..."
celery -A azure_advisor_reports worker \
    --loglevel=${CELERY_LOG_LEVEL:-info} \
    --concurrency=${CELERY_CONCURRENCY:-2} \
    --max-tasks-per-child=${CELERY_MAX_TASKS_PER_CHILD:-100} \
    --pool=threads \
    &

# Store Celery PID
CELERY_PID=$!

# Start Celery Beat scheduler in background (for periodic tasks)
echo "Starting Celery beat scheduler..."
celery -A azure_advisor_reports beat \
    --loglevel=${CELERY_LOG_LEVEL:-info} \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler \
    &

# Store Beat PID
BEAT_PID=$!

# Function to handle shutdown
shutdown() {
    echo "Shutting down services..."
    kill -TERM $CELERY_PID 2>/dev/null
    kill -TERM $BEAT_PID 2>/dev/null
    kill -TERM $GUNICORN_PID 2>/dev/null
    wait $CELERY_PID $BEAT_PID $GUNICORN_PID
    exit 0
}

# Trap SIGTERM and SIGINT (sh syntax: no SIG prefix)
trap shutdown TERM INT

# Start Gunicorn in foreground
echo "Starting Gunicorn server..."
gunicorn azure_advisor_reports.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers ${GUNICORN_WORKERS:-4} \
    --threads ${GUNICORN_THREADS:-2} \
    --worker-class gthread \
    --worker-tmp-dir /dev/shm \
    --timeout ${GUNICORN_TIMEOUT:-120} \
    --graceful-timeout ${GUNICORN_GRACEFUL_TIMEOUT:-30} \
    --max-requests ${GUNICORN_MAX_REQUESTS:-1000} \
    --max-requests-jitter ${GUNICORN_MAX_REQUESTS_JITTER:-50} \
    --access-logfile - \
    --error-logfile - \
    --log-level ${GUNICORN_LOG_LEVEL:-info} \
    --capture-output \
    --enable-stdio-inheritance &

# Store Gunicorn PID
GUNICORN_PID=$!

# Wait for all processes
wait $GUNICORN_PID
