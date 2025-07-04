import logging
from celery import shared_task
from confluent_kafka import Consumer
from django.conf import settings
import json

from kafka.handlers import handle_guild_war_game
from apps.saga.saga_orchestrator import handle_authorization_response

logger = logging.getLogger(__name__)

KAFKA_TOPICS = [
    'balance-reserve-events',
    'balance-compensate-events',
    'purchase-events',
    'scoreboard-events',
    'shop.inventory.updates',
]

KAFKA_CONFIG = {
    'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
    'group.id': 'shop-consumer-group',
    'auto.offset.reset': 'earliest',
}


def safe_json_decode(msg):
    try:
        return json.loads(msg.value().decode('utf-8'))
    except Exception as e:
        logger.error(f"[Kafka] JSON decode error: {e}")
        return None


@shared_task(bind=True)
def process_kafka_messages(self):
    """
    Celery-задача для бесконечного Kafka-консьюмера.
    """
    logger.info("[KafkaTask] Запуск Kafka consumer из Celery задачи...")

    consumer = Consumer(KAFKA_CONFIG)
    consumer.subscribe(KAFKA_TOPICS)

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue

            if msg.error():
                logger.error(f"[Kafka] Consumer error: {msg.error()}")
                continue

            data = safe_json_decode(msg)
            topic = msg.topic()

            if data is None:
                logger.warning(f"[Kafka] Пустое или неверное сообщение в топике: {topic}")
                continue

            logger.info(f"[Kafka] Получено сообщение из топика {topic}: {data}")

            try:
                if topic == 'purchase-events':
                    handle_guild_war_game(data)
                elif topic == 'scoreboard-events':
                    logger.info(f"[Kafka] Обработка события scoreboard: {data}")
                elif topic in ['balance-reserve-events', 'balance-compensate-events']:
                    handle_authorization_response(msg)
                else:
                    logger.warning(f"[Kafka] Неизвестный топик: {topic}")
            except Exception as e:
                logger.exception(f"[Kafka] Ошибка при обработке сообщения из {topic}: {e}")

    except Exception as e:
        logger.exception(f"[KafkaTask] Общая ошибка Kafka consumer: {e}")
    finally:
        consumer.close()
        logger.info("[KafkaTask] Kafka consumer остановлен")
