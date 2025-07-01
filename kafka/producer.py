import os
import json
import logging
from confluent_kafka import Producer

logger = logging.getLogger(__name__)

producer = Producer({
    'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')  # поправлено на стандартный порт Kafka
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


# def send_chest_promo_purchase_event(user_id: int):
#     """
#     Отправка события покупки сундука по акции.
#     """
#     topic = os.getenv('KAFKA_PURCHASE_TOPIC', 'purchase-events')
#     message = {
#         "user_id": user_id,
#         "event": "chest_promo_purchase"
#     }
#     producer.produce(
#         topic=topic,
#         value=json.dumps(message).encode('utf-8'),
#         callback=delivery_report
#     )
#     producer.flush()
