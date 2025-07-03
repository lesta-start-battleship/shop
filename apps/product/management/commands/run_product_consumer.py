import json
from django.core.management.base import BaseCommand
from confluent_kafka import KafkaException
from apps.product.models import Product
from config.settings import env
from config.kafka_config import get_consumer


class Command(BaseCommand):
	help = "Consume product events from Kafka and persist to DB"

	def handle(self, *args, **options):
		topic = env("KAFKA_PRODUCT_TOPIC")
		group_id = env("KAFKA_PRODUCT_GROUP")

		consumer = get_consumer(group_id)

		consumer.subscribe([topic])
		self.stdout.write(f"👂 Listening to `{topic}` on {env('KAFKA_BOOTSTRAP_SERVERS')}")

		try:
			while True:
				msg = consumer.poll(timeout=1.0)
				if msg is None:
					continue
				if msg.error():
					raise KafkaException(msg.error())

				try:
					data = json.loads(msg.value().decode("utf-8"))
				except json.JSONDecodeError:
					self.stderr.write("⚠️ Invalid JSON message, skipping.")
					continue

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
