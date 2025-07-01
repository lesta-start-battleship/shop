# shop

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
```