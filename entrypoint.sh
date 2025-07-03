#!/bin/bash
set -e


host="${POSTGRES_HOST:-db}"

echo "⏳ Waiting for PostgreSQL at host: $host..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$host" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q' 2>/dev/null; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "🟢 PostgreSQL is up"


echo "🔧 Applying migrations..."
python manage.py migrate --noinput

echo "🔄 Starting saga consumer..."
python manage.py run_saga_consumer &

echo "🔄 Starting product consumer..."
python manage.py run_product_consumer &


echo "🎯 Collecting static files..."
python manage.py collectstatic --noinput

echo "🚀 Starting Gunicorn..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000
