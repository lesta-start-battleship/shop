import logging
import random
from collections import defaultdict

from apps.chest.models import Chest

logger = logging.getLogger(__name__)


def open_chest(chest: Chest, amount: int):
    logger.info(f"Opening chest {chest.name}")
    chance = int(chest.item_probability)
    chest_products = list(chest.product.all())
    gold = int(chest.gold)
    amount = int(amount)
    rewards = {
        "products_id": defaultdict(int),
        "gold": 0,
        "callback_rewards": {},
        "chests": []
    }
    for i in range(0, amount):
        chest_name = chest.name
        if random.randrange(100) < chance:
            product = random.choice(chest_products)
            rewards["products_id"][product.id] += 1
            if product.name in rewards["callback_rewards"]:
                rewards["callback_rewards"][product.name]["amount"] += 1
            else:
                rewards["callback_rewards"][product.name] = {
                    "amount": 1,
                    "description": product.description
                }
        if chest.promotion:
            chest_name = "promo_chest"
        rewards["chests"].append((chest_name, chest.experience))
        rewards["gold"] += gold

    logger.info(f"Got {rewards} from {chest.name}")
    return rewards

