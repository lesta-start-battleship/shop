import logging
from celery import shared_task
from confluent_kafka import Consumer
from django.conf import settings
from .saga_orchestrator import safe_json_decode

from apps.chest.tasks import handle_guild_war_game
from kafka.handlers import handle_inventory_update
from .saga_orchestrator import (
    handle_authorization_response,
    handle_compensation_response,
    handle_promotion_compensation_response
)

logger = logging.getLogger(__name__)

KAFKA_TOPICS = [
    'auth.balance.reserve.response.shop',
    'auth.balance.compensate.response.shop',
    'balance-reserve-events',
    'balance-compensate-events',
    'purchase-events',
    'prod.shop.fact.chest-open.1',
    'shop.inventory.updates',
    'stage.game.fact.match-results.v1',
    'prod.scoreboard.fact.guild-war.1',
    'shop.inventory.updates',
    'promotion.compensation.commands'
]

KAFKA_CONFIG = {
    'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
    'group.id': 'shop-consumer-group',
    'auto.offset.reset': 'earliest',
}


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
                if topic in ['stage.game.fact.match-results.v1', 'prod.scoreboard.fact.guild-war.1']:
                    handle_guild_war_game(data)
                elif topic == 'prod.shop.fact.chest-open.1':
                    logger.info(f"[Kafka] Обработка события scoreboard: {data}")
                elif topic == 'auth.balance.reserve.response.shop':
                    handle_authorization_response(msg)
                elif topic == 'auth.balance.compensate.response.shop':
                    handle_compensation_response(msg)

                elif topic == 'shop.inventory.updates':
                    handle_inventory_update(data)

                elif topic == 'promotion.compensation.commands':
                    handle_promotion_compensation_response(msg)

                else:
                    logger.warning(f"[Kafka] Неизвестный топик: {topic}")

            except Exception as e:
                logger.exception(f"[Kafka] Ошибка при обработке сообщения из {topic}: {e}")

    except Exception as e:
        logger.exception(f"[KafkaTask] Общая ошибка Kafka consumer: {e}")

    finally:
        consumer.close()
        logger.info("[KafkaTask] Kafka consumer остановлен")
