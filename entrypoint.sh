#!/bin/sh

/wait-for-postgres.sh db
echo "🟢 PostgreSQL is up"

python manage.py migrate --noinput

# Run both consumers in the background
echo "🔄 Starting saga consumer..."
python manage.py run_saga_consumer &

echo "🔄 Starting product consumer..."
python manage.py run_product_consumer &

# Run the Django app via Gunicorn
echo "🚀 Starting Gunicorn..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000
