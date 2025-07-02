import os
from celery import Celery
from celery.signals import worker_ready

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@worker_ready.connect
def at_start(sender, **kwargs):
    """
    start Kafka consumer after worker started
    """
    from apps.purchase.tasks import process_kafka_messages
    process_kafka_messages.delay()


@worker_ready.connect
def on_worker_ready(sender, **kwargs):
    if sender.hostname.startswith('celery.kafka@'):
        from apps.purchase.tasks import process_kafka_messages
        sender.app.send_task('apps.purchase.tasks.process_kafka_messages')
