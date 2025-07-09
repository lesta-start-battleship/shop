import logging
logger = logging.getLogger(__name__)
from apps.chest.models import Chest
from apps.saga import saga_orchestrator

from .external import InventoryService

def compensate_promotion(promotion, request):
    if not promotion.has_ended():
        raise ValueError("Promotion is still active.")
    if promotion.compensation_done:
        raise ValueError("Already compensated.")

    logger.info(f"Starting compensation for Promotion ID {promotion.id}")

    chests = Chest.objects.filter(promotion=promotion)
    
    total_compensated = 0

    if not chests.exists():
        logger.warning(f"No chests linked to Promotion ID {promotion.id}. Nothing to compensate.")
        promotion.compensation_done = True
        promotion.save()
        return total_compensated

    
    for chest in chests:
        item_id = chest.item_id

        inventories = InventoryService.get_inventories_with_item(item_id=item_id, request=request)

        for inv in inventories:
            user_id = inv["user_id"]
            linked_items = inv.get("linked_items", [])
            
            for item in linked_items:
                quantity = item.get("amount", 0)
                amount = quantity * chest.cost

            logger.debug(f"Refunding {amount} gold to user {user_id} for {quantity} unopened chests (ID {item_id})")
            logger.info(f"Initiating async compensation for user {user_id}, amount {amount} gold")

            saga_orchestrator.publish_promotion_compensation(
                                        user_id=user_id,
                                        amount=amount,
                                        item_id=item_id,
                                    )
            
            total_compensated += quantity

    promotion.compensation_done = True
    promotion.save()

    logger.info(f"Completed compensation for Promotion ID {promotion.id}, total chests compensated: {total_compensated}")

    return total_compensated

