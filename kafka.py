import logging
from confluent_kafka import Producer
import json
import os

logger = logging.getLogger(__name__)

producer = Producer({
    'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', '37.9.53.228:9092')
})

def delivery_report(err, msg):
    if err is not None:
        logger.error(f"[Kafka] Delivery failed: {err}")
    else:
        logger.info(f"[Kafka] Delivered to {msg.topic()} [{msg.partition()}]")

def send_chest_promo_purchase_event(user_id: int):
    """
    Отправка события покупки сундука по акции.
    """
    topic = os.getenv('KAFKA_PURCHASE_TOPIC', 'purchase-events')
    message = {
        "user_id": user_id,
        "event": "chest_promo_purchase"
    }
    producer.produce(
        topic=topic,
        value=json.dumps(message).encode('utf-8'),
        callback=delivery_report
    )
    producer.flush()
