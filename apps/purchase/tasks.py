from celery import shared_task


from kafka.consumer import start_kafka_consumer
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_kafka_messages(self):
	try:
		logger.info("🔄 Запуск Kafka потребителя...")
		start_kafka_consumer()
	except Exception as exc:
		logger.error(f"❌ Ошибка в Kafka потребителе: {exc}")
		self.retry(exc=exc)


