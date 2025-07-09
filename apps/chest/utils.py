import logging
import random
import jwt
import requests

from collections import defaultdict
from django.db import close_old_connections
from config import settings

from apps.chest.models import Chest, ChestSettings

INVENTORY_API_URL = settings.INVENTORY_SERVICE_URL
logger = logging.getLogger(__name__)


def open_chest(chest: Chest, amount: int):
    logger.info(f"Opening chest {chest.name}")

    chest_settings = get_chest_settings()

    amount = int(amount)

    rewards = {
        "products_id": defaultdict(int),
        "gold": 0,
        # TODO if cli ask
        # "callback_rewards": {},
        "promo_chests": []
    }

    common_products = list(chest.product.all())
    if chest.name == chest_settings.black_pearl_chest:
        # Get items
        special_products = list(chest.special_products.all())

        deep_converter = next((p for p in special_products if chest_settings.davie_johns_product in p.name), None)
        spies = next((p for p in special_products if chest_settings.spies_product in p.name), None)
        for _ in range(amount):
            exp = 0
            roll = random.randint(1, 100)
            if roll <= 25:
                # Standard item
                product = random.choice(common_products)
                rewards["products_id"][product.item_id] += 1
            elif roll <= 50:
                # Experience
                exp = 10
            elif roll <= 75 and deep_converter:
                # Deep converter
                rewards["products_id"][deep_converter.item_id] += 1
            elif roll > 75 and spies:
                # Spies
                rewards["products_id"][spies.item_id] += 1
            if chest.promotion:
                rewards["promo_chests"].append((chest.promotion.id, exp))
    else:
        chance = int(chest.item_probability)
        gold = int(chest.gold)
        for _ in range(amount):
            if random.randrange(100) < chance:
                product = random.choice(common_products)
                rewards["products_id"][product.item_id] += 1
            #     if product.name in rewards["callback_rewards"]:
            #         rewards["callback_rewards"][product.name]["amount"] += 1
            #     else:
            #         rewards["callback_rewards"][product.name] = {
            #             "amount": 1,
            #             "description": product.description
            #         }
            if chest.promotion:
                promo_id = chest.promotion.id
                rewards["promo_chests"].append((promo_id, chest.experience))
            rewards["gold"] += gold

    logger.info(f"Got {rewards} from {chest.name}")
    return rewards


def generate_token(user_id, username="user", role="user"):
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
    }
    return jwt.encode(payload, key="", algorithm="none")


def generate_header(token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    return headers


def send_guild_war_reward(user_id: int, item_id: int, amount: int):
    """send reward"""
    url = f"{INVENTORY_API_URL}/inventory/add_item/"
    token = generate_token(user_id)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {"item_id": item_id, "amount": amount}

    for attempt in range(3):
        try:
            response = requests.patch(url, json=payload, headers=headers, timeout=5)
            response.raise_for_status()
            return
        except requests.RequestException as e:
            if attempt == 2:
                logger.error(f"Failed to send reward to {user_id}: {str(e)}")
        finally:
            close_old_connections()


def get_chest_settings():
    return ChestSettings.get_solo()
