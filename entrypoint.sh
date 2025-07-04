#!/bin/bash
set -e

host=${POSTGRES_HOST:-shop-db-1}
user=${POSTGRES_USER:-postgres}
db=${POSTGRES_DB:-postgres}
password=${POSTGRES_PASSWORD:-password}

echo "⏳ Ожидаем PostgreSQL на $host..."
until PGPASSWORD=$password psql -h "$host" -U "$user" -d "$db" -c "SELECT 1" >/dev/null 2>&1; do
  echo "PostgreSQL не доступна, ждем..."
  sleep 1
done
echo "🟢 PostgreSQL доступна"

echo "⏳ Ожидаем Redis..."
until redis-cli -h redis ping | grep -q PONG; do
  echo "Redis не доступен, ждем..."
  sleep 1
done
echo "🟢 Redis доступен"

echo "🔧 Применяем миграции..."
python manage.py makemigrations --noinput || true
python manage.py migrate --noinput

echo "📁 Собираем статические файлы..."
python manage.py collectstatic --noinput

if [ "$1" = "gunicorn" ]; then
  echo "🚀 Запускаем Gunicorn..."
  exec gunicorn config.wsgi:application --bind 0.0.0.0:8000

elif [ "$1" = "celery" ]; then
  echo "🚀 Запускаем Celery worker..."
  exec celery -A config worker --loglevel=info

elif [ "$1" = "beat" ]; then
  echo "🚀 Запускаем Celery beat..."
  exec celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler

else
  echo "❌ Неизвестная команда: $1"
  exit 1
fi
