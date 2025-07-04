import os
import json
import logging
from confluent_kafka import Producer

logger = logging.getLogger(__name__)

producer = Producer({
    'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
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


def send_chest_promo_open_kafka_event(user_id: int, quantity: int):
    send_kafka_message(
        os.getenv("KAFKA_SCOREBOARD_TOPIC", "scoreboard-events"),
        {
            "user_id": user_id,
            "event": "chest_promo_purchase",
            "quantity": quantity
        }
    )
