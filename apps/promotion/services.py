import logging
import requests
from django.conf import settings
logger = logging.getLogger(__name__)

INV_SERVICE_URL = settings.INV_SERVICE_URL


def promotion_has_ended(promotion):
    from django.utils.timezone import now
    return now() > (promotion.start_time + promotion.duration)
  
  
def fetch_chest_data(chest_id):
    """
    Retrieves chest details from Inventory Service.
    """
    
    endpoint = f"{INV_SERVICE_URL}/chest/{chest_id}/"
    
    try:
        response = requests.get(endpoint, timeout=5)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch chest {chest_id}: {response.text}")
            raise Exception("Chest not found or Inventory service error")

        return response.json()
    
    except requests.RequestException as e:
        logger.exception("Error fetching chest details from Inventory service")
        raise Exception("Failed to communicate with Inventory service") from e
    
    
def calculate_gold_for_chest(chest_id):
    """
    Fetches chest details and returns compensation value.
    """
    data = fetch_chest_data(chest_id)
    
    gold_amount = data.get("compensation_value", 50)
    logger.debug(f"Chest {chest_id} compensation_value: {gold_amount}")
    
    return gold_amount


def credit_gold(player_id, gold_amount):
    """
    Sends request to Inventory service to credit gold to a player.
    """
    endpoint = f"{INV_SERVICE_URL}/credit/"
    
    payload = {
        "player_id": player_id,
        "amount": gold_amount,
        "reason": "Promotion Chest Compensation"
    } # заглушка
    
    logger.info(f"Crediting {gold_amount} gold to player {player_id}")
    
    try:
        response = requests.post(endpoint, json=payload, timeout=5)
        
        if response.status_code != 200:
            logger.error(f"Failed to credit gold: {response.text}")
            raise Exception("Inventory service responded with an error")
        
        logger.debug(f"Gold successfully credited to player {player_id}")

    except requests.RequestException as e:
        logger.exception("Error communicating with Inventory service")
        raise Exception("Failed to communicate with Inventory service") from e


def compensate_unopened_chests(promotion):
    """
    Compensates all unopened, un-compensated chests from a specific promotion.
    """
    from apps.purchase.models import Purchase  # Local import to avoid circular dependency
    
    purchases = Purchase.objects.filter(
        promotion_id=promotion.id,
        chest_id__isnull=False,
        chest_opened=False,
        compensated=False
    )

    count = 0
    
    for purchase in purchases:
        gold_amount = calculate_gold_for_chest(purchase.chest_id)
        credit_gold(purchase.owner, gold_amount)

        purchase.compensated = True
        purchase.save()
        count += 1

    logger.info(f"Compensated {count} unopened chests for promotion {promotion.id}")
    return count


