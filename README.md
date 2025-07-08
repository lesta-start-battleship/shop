## .env example


```dotenv
# Django
DEBUG=False
SECRET_KEY=your-secret-key-here

# Postgres
POSTGRES_USER=shop_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=your_database_name
POSTGRES_HOST=shop-db-1
POSTGRES_PORT=5432

# Kafka (внешний)
KAFKA_BOOTSTRAP_SERVERS=37.9.53.228:9092
KAFKA_PURCHASE_TOPIC=purchase-events
KAFKA_TOPIC_AUTH_RESERVE=auth.balance.reserve.response.shop
KAFKA_TOPIC_INVENTORY_ADD=inventory-add
KAFKA_TOPIC_AUTH_COMMIT=auth-commit
KAFKA_SCOREBOARD_TOPIC=prod.shop.fact.chest-open.1
KAFKA_PRODUCT_GROUP=inventory-group
KAFKA_PRODUCT_TOPIC=shop.inventory.updates
KAFKA_CHEST_EVENTS_TOPIC=prod.shop.fact.chest-open.1

# Celery (REDIS)
REDIS_HOST=redis
REDIS_PORT=6379

# CORS
CORS_ALLOWED_ORIGINS=http://CLI_IP:CLI_PORT

INVENTORY_SERVICE_URL=http://37.9.53.107/
```

# Shop Microservice

Микросервис "Магазин" для игры "Морской бой".

---


## Установка и запуск

1. Клонировать репозиторий:

```bash
git clone https://github.com/sendy-tech/shop.git
cd shop
git checkout dev
```

2. Запустить Docker Compose:

```bash
docker-compose up --build
```

3. Войти в контейнер и применить миграции:
```bash
docker-compose exec shop python manage.py migrate
```

4. Запустить тесты:
```bash
docker-compose exec shop python manage.py test
```
