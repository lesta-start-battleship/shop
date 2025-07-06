import logging
from celery import shared_task
from confluent_kafka import Consumer
from django.conf import settings
from .saga_orchestrator import safe_json_decode

from apps.chest.tasks import handle_guild_war_game
from kafka.handlers import handle_inventory_update
from .saga_orchestrator import (
    handle_authorization_response,
    handle_compensation_response
)

logger = logging.getLogger(__name__)

KAFKA_TOPICS = [
    'balance-responses',
    'compensation-responses',
    'stage.game.fact.match-results.v1',
    'prod.scoreboard.fact.guild-war.1',
    'shop.inventory.updates',
]

KAFKA_CONFIG = {
    'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
    'group.id': 'shop-consumer-group',
    'auto.offset.reset': 'earliest',
}


@shared_task(bind=True)
def process_kafka_messages(self):
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
                if topic in ['stage.game.fact.match-results.v1', 'prod.scoreboard.fact.guild-war.1']:
                    handle_guild_war_game(data)

                elif topic == 'balance-responses':
                    handle_authorization_response(msg)

                elif topic == 'compensation-responses':
                    handle_compensation_response(msg)

                elif topic == 'shop.inventory.updates':
                    handle_inventory_update(data)

                else:
                    logger.warning(f"[Kafka] Неизвестный топик: {topic}")

            except Exception as e:
                logger.exception(f"[Kafka] Ошибка при обработке сообщения из {topic}: {e}")

    except Exception as e:
        logger.exception(f"[KafkaTask] Общая ошибка Kafka consumer: {e}")

    finally:
        consumer.close()
        logger.info("[KafkaTask] Kafka consumer остановлен")
