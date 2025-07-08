import logging

from apps.product.models import Product

logger = logging.getLogger(__name__)


def handle_inventory_update(event: dict):
	item_id = event.get("id")
	if not item_id:
		logger.error(f"[Kafka] Missing item ID in inventory update: {event}")
		return

	shop_item_id = event.get("shop_item_id")
	if shop_item_id == 1:
		logger.info(f"[Kafka] Skipped saving product with item_id {item_id} due to shop_item_id being 1")
		return

	try:
		product, created = Product.objects.update_or_create(
			item_id=item_id,
			defaults={
				'name': event.get('name', ''),
				'description': event.get('description', ''),
				'currency_type': event.get('currency_type'),
				'kind': event.get('kind'),
			}
		)
		action = "Created" if created else "Updated"
		logger.info(f"[Kafka] {action} product #{product.id} (Item ID: {item_id}): {product.name}")

	except Exception as e:
		logger.exception(f"[Kafka] Failed to process inventory update for item {item_id}: {e}")
