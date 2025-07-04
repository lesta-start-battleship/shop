import json
import logging
import os

from confluent_kafka import Consumer, KafkaError
from apps.saga.saga_orchestrator import (
	handle_authorization_response,
	handle_compensation_response
)

logger = logging.getLogger(__name__)


def get_saga_consumer():
	"""Create dedicated consumer for Saga topics"""
	return Consumer({
		'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
		'group.id': 'saga-orchestrator-group',
		'auto.offset.reset': 'earliest'
	})


def start_saga_consumer():
	"""Main consumer function for Saga events only"""
	logger.info("🚀 Starting Saga Orchestrator Consumer...")

	SAGA_TOPICS = [
		'balance-reserve-events',  # Authorization responses
		'balance-compensate-events'  # Compensation responses
	]

	consumer = None
	try:
		consumer = get_saga_consumer()
		consumer.subscribe(SAGA_TOPICS)
		logger.info(f"✅ Subscribed to Saga topics: {', '.join(SAGA_TOPICS)}")

		while True:
			msg = consumer.poll(1.0)
			if msg is None:
				continue

			if msg.error():
				if msg.error().code() == KafkaError._PARTITION_EOF:
					continue
				logger.error(f"⚠️ Kafka error: {msg.error()}")
				continue

			try:
				event = json.loads(msg.value().decode('utf-8'))
				if msg.topic() == 'balance-reserve-events':
					handle_authorization_response(msg)
				elif msg.topic() == 'balance-compensate-events':
					handle_compensation_response(msg)

			except json.JSONDecodeError:
				logger.error("❌ Invalid JSON message")
			except Exception as e:
				logger.error(f"⛔ Error processing message: {e}")

	except KeyboardInterrupt:
		logger.info("🛑 Shutting down consumer...")
	except Exception as e:
		logger.error(f"⛔ Consumer error: {e}", exc_info=True)
	finally:
		if consumer:
			consumer.close()
		logger.info("🔌 Saga consumer stopped")
