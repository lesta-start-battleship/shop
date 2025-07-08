import requests
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.chest.models import Chest
from config import settings

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Chest)
def set_chest_item_id(sender, instance, created, **kwargs):
    """
    Add item_id from inventory service
    """
    INVENTORY_API_URL = settings.INVENTORY_SERVICE_URL

    inventory_create_item_url = f"{INVENTORY_API_URL}/items/create/"

    headers = {
        "Authorization": f"Bearer ",
        "Content-Type": "application/json"
    }

    if created and not instance.item_id:
        payload = {
            "name": instance.name,
            "description": f"Сундук {instance.name}",
            "script": "string",
            "use_limit": 0,
            "cooldown": 0,
            "kind": "расходник",
            "shop_item_id": 0
        }

        try:
            response = requests.post(
                inventory_create_item_url,
                json=payload,
                timeout=5,
                headers=headers,
            )
            response.raise_for_status()
            response_data = response.json()

            Chest.objects.filter(pk=instance.pk).update(
                item_id=response_data["id"]
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for Chest {instance.id}: {str(e)}")
