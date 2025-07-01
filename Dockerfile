# === build stage ===
FROM python:3.11-slim AS build
WORKDIR /code
# …установка gcc, libpq-dev, pip install…
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

# === final stage ===
FROM python:3.11-slim
WORKDIR /code

# переменные окружения…
RUN apt-get update && apt-get install -y postgresql-client

# копируем зависимости из билд-стейджа
COPY --from=build /install /usr/local

# копируем код приложения
COPY . /code

# **ВАЖНО**: копируем скрипты в корень
COPY scripts/wait-for-postgres.sh /wait-for-postgres.sh
COPY entrypoint.sh              /entrypoint.sh

# делаем их исполняемыми
RUN chmod +x /wait-for-postgres.sh /entrypoint.sh

# собираем статику
RUN python manage.py collectstatic --noinput

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
