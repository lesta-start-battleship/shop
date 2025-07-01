import requests
import os
import logging

logger = logging.getLogger(__name__)

SCOREBOARD_SERVICE_URL = os.getenv('SCOREBOARD_SERVICE_URL', 'http://SCOREBOARD-service.local/api/purchases/')

def send_chest_promo_purchase_event(user_id: int, quantity: int):
    """
    Отправка POST-запроса в сервис промо о покупке сундуков по акции.
    """
    payload = {
        "user_id": user_id,
        "event": "chest_promo_purchase",
        "quantity": quantity,
    }
    try:
        response = requests.post(SCOREBOARD_SERVICE_URL, json=payload, timeout=5)
        response.raise_for_status()
        logger.info(f"[SCOREBOARD API] Purchase event sent successfully for user {user_id}, qty {quantity}")
        return True
    except requests.RequestException as e:
        logger.error(f"[SCOREBOARD API] Failed to send purchase event: {e}")
        return False
