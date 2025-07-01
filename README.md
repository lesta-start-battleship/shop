## .env example


```dotenv
DEBUG=False
SECRET_KEY=your-secret-key-here

POSTGRES_USER=shop_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=your_database_name
POSTGRES_HOST=shop-db-1
POSTGRES_PORT=5432

KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_PURCHASE_TOPIC=purchase-events
KAFKA_TOPIC_AUTH_RESERVE=auth-reserve
KAFKA_TOPIC_INVENTORY_ADD=inventory-add
KAFKA_TOPIC_AUTH_COMMIT=auth-commit

SCOREBOARD_SERVICE_URL=http://7group_IP/api/purchases/
INVENTORY_SERVICE_URL=http://inventory/api
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
