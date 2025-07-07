import logging
logger = logging.getLogger(__name__)
from apps.chest.models import Chest
from apps.saga import saga_orchestrator

from .external import InventoryService

def compensate_promotion(promotion):
    if not promotion.has_ended():
        raise ValueError("Promotion is still active.")
    if promotion.compensation_done:
        raise ValueError("Already compensated.")

    logger.info(f"Starting compensation for Promotion ID {promotion.id}")

    chest_ids = Chest.objects.filter(promotion=promotion).values_list('id', flat=True)
    
    total_compensated = 0

    if not chest_ids:
        logger.warning(f"No chests linked to Promotion ID {promotion.id}. Nothing to compensate.")
        promotion.compensation_done = True
        promotion.save()
        return total_compensated

    
    for chest_id in chest_ids:
        chest = Chest.objects.get(id=chest_id)

        inventories = InventoryService.get_inventories_with_item(chest_id)

        for inv in inventories:
            user_id = inv["user_id"]
            quantity = inv["quantity"]
            amount = quantity * chest.cost

            logger.debug(f"Refunding {amount} gold to user {user_id} for {quantity} unopened chests (ID {chest.id})")
            logger.info(f"Initiating async compensation for user {user_id}, amount {amount} gold")

            saga_orchestrator.publish_promotion_compensation(
                                        user_id=user_id,
                                        amount=amount,
                                        item_id=chest.id,
                                    )
            
            total_compensated += quantity

    promotion.compensation_done = True
    promotion.save()

    logger.info(f"Completed compensation for Promotion ID {promotion.id}, total chests compensated: {total_compensated}")

    return total_compensated

