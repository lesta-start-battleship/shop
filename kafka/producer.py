import os
import json
import logging
from confluent_kafka import Producer

logger = logging.getLogger(__name__)

producer = Producer({
    'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
})

def delivery_report(err, msg):
    if err is not None:
        logger.error(f"[Kafka] Delivery failed: {err}")
    else:
        logger.info(f"[Kafka] Message delivered to {msg.topic()} [{msg.partition()}]")


def send_kafka_message(topic: str, message: dict):
    """
    Универсальная функция отправки события в Kafka.
    """
    try:
        serialized = json.dumps(message).encode('utf-8')
        producer.produce(topic=topic, value=serialized, callback=delivery_report)
        producer.flush()
        logger.info(f"[Kafka] Sent message to topic '{topic}': {message}")
    except Exception as e:
        logger.exception(f"[Kafka] Failed to send message to topic '{topic}': {e}")

def send_chest_promo_purchase_kafka_event(user_id: int, quantity: int):
    message = {
        "user_id": user_id,
        "event": "chest_promo_purchase",
        "quantity": quantity
    }

    try:
        producer.produce(os.getenv("KAFKA_SCOREBOARD_TOPIC", "scoreboard-events"), key=str(user_id), value=json.dumps(message))
        producer.flush(3)
        logger.info(f"[KAFKA] Event sent for user {user_id}, qty {quantity}")
    except Exception as e:
        logger.error(f"[KAFKA] Failed to send event: {e}")
