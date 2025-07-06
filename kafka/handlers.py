import logging
from apps.product.models import Product

logger = logging.getLogger(__name__)


def handle_inventory_update(event: dict):
    product_id = event.get("id")
    if not product_id:
        logger.error(f"[Kafka] Missing product ID in inventory update: {event}")
        return

    try:
        product, created = Product.objects.update_or_create(
            id=product_id,
            defaults={
                'name': event.get('name', ''),
                'description': event.get('description', ''),
                'currency_type': event.get('currency_type'),
            }
        )
        action = "Created" if created else "Updated"
        logger.info(f"[Kafka] {action} product #{product.id}: {product.name}")

    except Exception as e:
        logger.exception(f"[Kafka] Failed to process inventory update: {e}")
