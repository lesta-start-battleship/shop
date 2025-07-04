import logging
logger = logging.getLogger(__name__)


from .external import InventoryService, AuthService

def compensate_promotion(promotion):
    if not promotion.has_ended():
        raise ValueError("Promotion is still active.")
    if promotion.compensation_done:
        raise ValueError("Already compensated.")

    logger.info(f"Starting compensation for Promotion ID {promotion.id}")

    item_ids = list(promotion.chests.values_list('id', flat=True)) + list(
        promotion.products.values_list('id', flat=True)
    )

    total_compensated = 0
    for item_id in item_ids:
        logger.info(f"Processing item ID {item_id} for compensation.")

        inventories = InventoryService.get_inventories_with_item(item_id)

        for inv in inventories:
            user_id = inv['user_id']
            quantity = inv['quantity']
            amount = quantity * 100  # Example

            logger.debug(f"Compensating user {user_id} with {amount} gold for item {item_id} (quantity: {quantity})")

            AuthService.compensate_balance(user_id, amount, "gold")
            total_compensated += quantity

        InventoryService.delete_item(item_id)
        logger.info(f"Deleted item {item_id} from inventory after compensation.")

    promotion.compensation_done = True
    promotion.save()

    logger.info(f"Completed compensation for Promotion ID {promotion.id}, total items compensated: {total_compensated}")

    return total_compensated


