import logging

from apps.product.models import Product

logger = logging.getLogger(__name__)


def handle_guild_war_game(event: dict):
	# TODO
	"""
	test_hanlder
	"""
	user = event.get("user_id")
	place = event.get("place")

	if not all([user, place]):
		logger.error(f"{event}")
		return

	logger.info(f"[Kafka]  guild war game win {user} place -> {place}")



def handle_inventory_update(event: dict):
	product_id = event.get("id")
	if not product_id:
		logger.error(f"[Kafka] ❌ 'id' is required in event: {event}")
		return

	try:
		product, created = Product.objects.update_or_create(
			id=product_id,
			defaults={
				'name': event.get('name', ''),
				'description': event.get('description', ''),
				'currency_type': event.get('currency_type')
			}
		)
		if created:
			logger.info(f"[Kafka] ✅ Created new product: {product.name} (ID: {product.id})")
		else:
			logger.info(f"[Kafka] ♻️ Updated product: {product.name} (ID: {product.id})")

	except Exception as e:
		logger.exception(f"[Kafka] ❌ Failed to update/create product: {e}")
