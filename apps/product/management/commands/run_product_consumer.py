import os, json
from django.core.management.base import BaseCommand
from confluent_kafka import Consumer, KafkaException

from apps.product.models import Product


class Command(BaseCommand):
    help = "Consume product events from Kafka and persist to DB"

    def handle(self, *args, **options):
        conf = {
            'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
            'group.id': os.getenv('KAFKA_PRODUCT_GROUP'),
            'auto.offset.reset': 'earliest',
        }
        consumer = Consumer(conf)

        topic = os.getenv('KAFKA_PRODUCT_TOPIC')
        consumer.subscribe([topic])
        self.stdout.write(f"👂 Listening to `{topic}` on {conf['bootstrap.servers']}")

        try:
            while True:
                msg = consumer.poll(timeout=1.0)
                if msg is None:
                    continue
                if msg.error():
                    raise KafkaException(msg.error())

                data = json.loads(msg.value().decode('utf-8'))

                product, created = Product.objects.update_or_create(
                    name=data['name'],
                    defaults={
                        'description': data.get('description', ''),
                    }
                )

                self.stdout.write(f"{'✅ Created' if created else '🔄 Updated'} Product: {product.name}")

        except Exception as e:
            self.stderr.write(f"❌ Consumer error: {e}")
        finally:
            consumer.close()
            self.stdout.write("🛑 Consumer closed")
