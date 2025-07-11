import os
import json
import logging
from confluent_kafka import Producer
from django.conf import settings

logger = logging.getLogger(__name__)

producer = Producer({
    'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS
})


def delivery_report(err, msg):
    if err:
        logger.error(f"[Kafka] Delivery failed: {err}")
    else:
        logger.info(f"[Kafka] Delivered to {msg.topic()} [{msg.partition()}]")


def send_kafka_message(topic: str, message: dict):
    try:
        value = json.dumps(message).encode('utf-8')
        producer.produce(topic=topic, value=value, callback=delivery_report)
        producer.flush()
    except Exception as e:
        logger.exception(f"[Kafka] Failed to send message to {topic}: {e}")
