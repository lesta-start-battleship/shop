from celery import shared_task

from kafka.consumer import start_kafka_consumer


@shared_task
def process_kafka_messages():
    start_kafka_consumer()
