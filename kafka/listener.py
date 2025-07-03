import os
import json
import logging
from confluent_kafka import Consumer, KafkaException

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.purchase.models import Purchase
from kafka.producer import send_kafka_message
from kafka.handlers import (
    handle_auth_reserve_result,
    handle_inventory_result,
    handle_auth_commit_result,
)

logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
GROUP_ID = os.getenv("KAFKA_CONSUMER_GROUP", "shop-service-group")

TOPIC_HANDLERS = {
    "auth-reserve-result": handle_auth_reserve_result,
    "inventory-add-result": handle_inventory_result,
    "auth-commit-result": handle_auth_commit_result,
}


class Command(BaseCommand):
    help = "Запуск Kafka consumer'а для обработки событий саги покупки"

    def handle(self, *args, **options):
        consumer = Consumer({
            'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
            'group.id': GROUP_ID,
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': False,
        })

        topics = list(TOPIC_HANDLERS.keys())
        consumer.subscribe(topics)
        self.stdout.write(self.style.SUCCESS(f"Subscribed to Kafka topics: {topics}"))

        try:
            while True:
                msg = consumer.poll(1.0)

                if msg is None:
                    continue
                if msg.error():
                    raise KafkaException(msg.error())

                topic = msg.topic()
                value = msg.value().decode('utf-8')
                logger.debug(f"[Kafka] Received message from {topic}: {value}")

                try:
                    event = json.loads(value)
                    handler = TOPIC_HANDLERS.get(topic)
                    if handler:
                        with transaction.atomic():
                            handler(event)
                        consumer.commit(msg)  # Коммитим offset после успешной обработки
                    else:
                        logger.warning(f"No handler for topic: {topic}")
                except Exception as e:
                    logger.exception(f"Failed to process message from {topic}: {e}")

        except KeyboardInterrupt:
            pass
        finally:
            consumer.close()
            self.stdout.write(self.style.SUCCESS("Kafka consumer stopped gracefully."))