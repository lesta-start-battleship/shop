# 🛒 Shop Microservice — Battleship Game

Микросервис **магазина** для многопользовательской игры **"Морской бой"**. 
Отвечает за управление сундуками и акциями. 
Встроена интеграция с Kafka, Celery и Redis.

---

## 📦 Возможности

- Покупка предметов и сундуков
- Открытие сундуков и получение наград
- Акции и компенсации
- Kafka-события и оркестрация через Saga
- Обработка асинхронных задач через Celery
- Интеграция с другими микросервисами: 
authentication, inventory, scoreboard

---

## 🛠️ Стек технологий

| Компонент     | Технология                    |
|---------------|-------------------------------|
| Backend       | Django / Django REST Framework |
| Асинхронность | Celery + Redis                |
| Брокер событий| Kafka                         |
| База данных   | PostgreSQL                    |
| Докеризация   | Docker + Docker Compose       |
| Мониторинг    | Prometheus      |

---

## 📁 Структура репозитория

```
shop/
├── apps/
│   ├── chest/        # сундуки
│   ├── product/      # товары
│   ├── promotion/    # акции
│   ├── purchase/     # покупки
│   └── saga/         # оркестрация транзакций
├── kafka/            # обработчики kafka-сообщений
├── config/           # Django settings
├── docker-compose.yml
├── requirements.txt
└── manage.py
```

---

## ⚙️ Быстрый старт

### 1. Клонировать репозиторий

```bash
git clone https://github.com/lesta-start-battleship/shop.git
cd shop
git checkout dev
```

### 2. Настроить `.env`

Создай `.env` по примеру:

<details>
<summary>📄 .env example</summary>

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

# Kafka (внешний брокер)
KAFKA_BOOTSTRAP_SERVERS=37.9.53.228:9092
KAFKA_PURCHASE_TOPIC=purchase-events
KAFKA_TOPIC_AUTH_RESERVE=auth.balance.reserve.response.shop
KAFKA_TOPIC_INVENTORY_ADD=inventory-add
KAFKA_TOPIC_AUTH_COMMIT=auth-commit
KAFKA_SCOREBOARD_TOPIC=prod.shop.fact.chest-open.1
KAFKA_PRODUCT_GROUP=inventory-group
KAFKA_PRODUCT_TOPIC=shop.inventory.updates
KAFKA_CHEST_EVENTS_TOPIC=prod.shop.fact.chest-open.1

# Redis (Celery)
REDIS_HOST=redis
REDIS_PORT=6379

# CORS
CORS_ALLOWED_ORIGINS=CORS

# Сервисы
INVENTORY_SERVICE_URL=inventory
```

</details>

### 3. Запустить микросервис

```bash
docker-compose up --build
```


### 4. Запустить тесты

```bash
docker-compose exec shop python manage.py test
```

---

## 🔌 Эндпоинты

| Метод | URL                     | Описание                    |
|-------|-------------------------|-----------------------------|
| GET   | `/item/`                | Доступные товары            |
| GET   | `/chest/`               | Доступные сундуки           |
| GET   | `/promotion/`           | Доступные акции             |
| POST  | `/item/{item_id}/buy`   | Купить предмет              |
| POST  | `/chest/{chest_id}/buy` | Купить сундук               |
| POST  | `/chest/open/`          | Открыть сундук              |
| GET   | `/purchase/`            | Список покупок пользователя |
| GET   | `/admin/chest/`         | Просмотр сундуков (админка) |
| POST  | `/admin/products/`      | Создать сундук (админка)     |


---

## 📬 Входящие Kafka-топики

| Топик                                           | Описание                     |
|------------------------------------------------|------------------------------|
| `auth.balance.reserve.response.shop`           | Ответ от сервиса авторизации |
| `auth.balance.compensate.response.shop`        | Компенсация после отмены     |
| `shop.inventory.updates`                       | Обновление инвентаря         |
| `stage.game.fact.match-results.v1`             | Результаты матчей (сундуки)  |
| `prod.scoreboard.fact.guild-war.1`             | Событие войны гильдий        |
| `promotion.compensation.commands`              | Компенсации по акциям        |

---

## ✅ Проверка здоровья

- `GET /metrics` — метрики Prometheus

---