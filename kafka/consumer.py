import os
import json
import logging
from confluent_kafka import Consumer, KafkaError

from kafka.handlers import (
    handle_guild_war_game,
handle_inventory_update
)

# from apps.saga.saga_orchestrator import (
#     handle_authorization_response
# )

logger = logging.getLogger(__name__)

TOPICS = [
    os.getenv('KAFKA_TOPIC_AUTH_RESERVE_RESULT', 'auth-reserve-result'),
    os.getenv('KAFKA_TOPIC_AUTH_COMMIT_RESULT', 'auth-commit-result'),
    os.getenv('KAFKA_PURCHASE_TOPIC', 'guild.wars.results'),
    os.getenv("KAFKA_SCOREBOARD_TOPIC", "scoreboard-events"),
    os.getenv("KAFKA_TOPIC_INVENTORY_UPDATES", "shop.inventory.updates"),
]

consumer_conf = {
    'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
    'group.id': 'shop-consumer-group',
    'auto.offset.reset': 'earliest'
}


def start_kafka_consumer():
    consumer = Consumer(consumer_conf)
    consumer.subscribe(TOPICS)

    logger.info(f"[Kafka] Subscribed to topics: {TOPICS}")

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    logger.error(f"[Kafka] Consumer error: {msg.error()}")
                    continue

            try:
                event = json.loads(msg.value().decode('utf-8'))
                topic = msg.topic()
                logger.info(f"[Kafka] start_kafka_consumer() here")
                logger.info(f"[Kafka] Received message on topic {topic}: {event}")

                if topic.endswith("auth-reserve-result"):
                    pass
                    # handle_authorization_response(event)
                # elif topic.endswith("auth-commit-result"):
                #     handle_auth_commit_result(event)
                elif topic.endswith("guild.wars.results"):
                    handle_guild_war_game(event)
                elif topic.endswith("shop.inventory.updates"):
                    handle_inventory_update(event)
                else:
                    logger.warning(f"[Kafka] Unknown topic: {topic}")

            except Exception as e:
                logger.exception(f"[Kafka] Error processing message: {e}")

    except KeyboardInterrupt:
        logger.info("[Kafka] Stopping consumer (KeyboardInterrupt)")

    finally:
        consumer.close()
