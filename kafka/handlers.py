import logging
from django.db import transaction

from kafka.producer import send_kafka_message
from apps.purchase.models import Purchase, TransactionStatus

logger = logging.getLogger(__name__)


def handle_auth_reserve_result(event: dict):
    """
    Обрабатывает результат резервирования средств из auth-сервиса.
    """
    purchase_id = event.get("purchase_id")
    success = event.get("success")
    transaction_id = event.get("transaction_id")

    if not all([purchase_id, transaction_id]):
        logger.error(f"[Kafka] Missing required fields in auth-reserve-result: {event}")
        return

    try:
        purchase = Purchase.objects.get(id=purchase_id)
    except Purchase.DoesNotExist:
        logger.error(f"[Kafka] Purchase with id {purchase_id} not found")
        return

    if success:
        purchase.transaction_status = TransactionStatus.RESERVED
        purchase.save(update_fields=["transaction_status"])
        logger.info(f"[Kafka] Purchase {purchase_id} -> RESERVED")

        send_kafka_message("inventory-add", {
            "user_id": purchase.owner,
            "product_id": purchase.item.id,
            "transaction_id": transaction_id,
            "purchase_id": purchase.id
        })
        logger.info(f"[Kafka] Sent inventory-add for purchase {purchase.id}")
    else:
        purchase.transaction_status = TransactionStatus.DECLINED
        purchase.save(update_fields=["transaction_status"])
        logger.warning(f"[Kafka] Purchase {purchase_id} -> DECLINED")


def handle_inventory_result(event: dict):
    """
    Обрабатывает результат добавления товара в инвентарь.
    """
    purchase_id = event.get("purchase_id")
    success = event.get("success")
    transaction_id = event.get("transaction_id")

    if not all([purchase_id, transaction_id]):
        logger.error(f"[Kafka] Missing required fields in inventory-result: {event}")
        return

    try:
        purchase = Purchase.objects.get(id=purchase_id)
    except Purchase.DoesNotExist:
        logger.error(f"[Kafka] Purchase with id {purchase_id} not found")
        return

    if success:
        send_kafka_message("auth-commit", {
            "transaction_id": transaction_id,
            "purchase_id": purchase.id
        })
        logger.info(f"[Kafka] Sent auth-commit for purchase {purchase.id}")
    else:
        purchase.transaction_status = TransactionStatus.FAILED
        purchase.save(update_fields=["transaction_status"])
        logger.warning(f"[Kafka] Purchase {purchase.id} -> FAILED (inventory error)")


def handle_auth_commit_result(event: dict):
    """
    Обрабатывает результат финального списания средств.
    """
    purchase_id = event.get("purchase_id")
    success = event.get("success")

    if not purchase_id:
        logger.error(f"[Kafka] Missing purchase_id in auth-commit-result: {event}")
        return

    try:
        purchase = Purchase.objects.get(id=purchase_id)
    except Purchase.DoesNotExist:
        logger.error(f"[Kafka] Purchase with id {purchase_id} not found")
        return

    if success:
        purchase.transaction_status = TransactionStatus.COMPLETED
        logger.info(f"[Kafka] Purchase {purchase.id} -> COMPLETED")
    else:
        purchase.transaction_status = TransactionStatus.FAILED
        logger.warning(f"[Kafka] Purchase {purchase.id} -> FAILED (auth commit)")

    purchase.save(update_fields=["transaction_status"])


def handle_guild_war_game(event: dict):
    # TODO
    """
    test_hanlder
    """
    user = event.get("user_id")
    place = event.get("place")

    if not all([user, place]):
        logger.error(f"{event}")
        return

    logger.info(f"[Kafka]  guild war game win {user} place -> {place}")