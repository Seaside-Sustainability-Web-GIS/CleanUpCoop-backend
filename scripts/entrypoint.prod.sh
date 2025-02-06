#!/bin/sh

# Wait for PostgreSQL to be ready
echo "Waiting for database..."
while ! nc -z db 5432; do
  sleep 1
done
echo "PostgreSQL started, running migrations..."

# Run migrations & collect static files
python manage.py collectstatic --noinput
python manage.py migrate --noinput

echo "Starting Django server..."
# Start Uvicorn server
exec uvicorn WebGIS.asgi:application --host 0.0.0.0 --port 8000 --workers 4
