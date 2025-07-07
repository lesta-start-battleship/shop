import os, logging, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from celery import Celery
from celery.signals import worker_ready

logger = logging.getLogger(__name__)

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@worker_ready.connect
def start_kafka_consumer(sender, **kwargs):
    """
    Запускаем Kafka-консьюмер при старте Celery worker.
    """
    try:
        from apps.saga.tasks import process_kafka_messages
        logger.info("[Celery] Worker ready — запускаем Kafka consumer...")
        process_kafka_messages.delay()
    except Exception as e:
        logger.exception(f"[Celery] Ошибка при запуске Kafka consumer: {e}")
