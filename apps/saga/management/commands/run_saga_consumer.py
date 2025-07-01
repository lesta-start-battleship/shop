import os
import json
from django.core.management.base import BaseCommand
from confluent_kafka import Consumer, KafkaException
from apps.saga.models import SagaOrchestrator


class Command(BaseCommand):
    help = "Consume saga events from Kafka and process them"

    def handle(self, *args, **options):
        conf = {
            'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092'),
            'group.id': os.getenv('KAFKA_SAGA_GROUP', 'saga-group'),
            'auto.offset.reset': 'earliest',
        }

        topics = [
            'balance-reserve-events',
            'inventory-update-events',
            'balance-compensate-events'
        ]

        consumer = Consumer(conf)
        consumer.subscribe(topics)

        self.stdout.write(f"👂 Subscribed to topics: {topics}")

        try:
            while True:
                msg = consumer.poll(timeout=1.0)
                if msg is None:
                    continue
                if msg.error():
                    raise KafkaException(msg.error())

                try:
                    raw = msg.value().decode('utf-8')
                    event = json.loads(raw)
                except json.JSONDecodeError:
                    self.stderr.write(f"⚠️  Invalid JSON, skipping: {msg.value()}")
                    continue

                topic = msg.topic()
                transaction_id = event.get('transaction_id')
                success = event.get('success', False)

                if not transaction_id:
                    self.stderr.write(f"⚠️  Missing transaction_id in event: {event}")
                    continue

                try:
                    saga = SagaOrchestrator.objects.get(transaction_id=transaction_id)

                    if topic == 'balance-reserve-events':
                        saga.handle_balance_response(success, event)

                    elif topic == 'inventory-update-events':
                        saga.handle_inventory_response(success, event)

                    elif topic == 'balance-compensate-events':
                        saga.handle_compensation_response(success, event)

                    self.stdout.write(f"✅ Processed event for `{transaction_id}` from topic `{topic}`")

                except SagaOrchestrator.DoesNotExist:
                    self.stderr.write(f"❌ Saga with ID `{transaction_id}` not found.")
                except Exception as e:
                    self.stderr.write(f"❌ Error while handling event: {e}")

        except Exception as e:
            self.stderr.write(f"❌ Kafka consumer error: {e}")
        finally:
            consumer.close()
            self.stdout.write("🛑 Saga consumer closed")
