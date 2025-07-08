import os, logging
from celery import Celery
from celery.signals import worker_ready

logger = logging.getLogger(__name__)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@worker_ready.connect
def start_kafka_consumer(sender, **kwargs):
	import django
	django.setup()
	try:
		from apps.saga.tasks import process_kafka_messages
		logger.info("[Celery] Worker ready — запускаем Kafka consumer...")
		process_kafka_messages.delay()
	except Exception as e:
		logger.exception(f"[Celery] Ошибка при запуске Kafka consumer: {e}")
