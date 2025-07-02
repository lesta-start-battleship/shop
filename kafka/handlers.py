import logging

from kafka.producer import send_kafka_message
from apps.saga.models import SagaOrchestrator

logger = logging.getLogger(__name__)


def handle_auth_reserve_result(event: dict):
    """
    Обрабатывает результат резервирования средств из auth-сервиса.
    """
    success = event.get("success")
    transaction_id = event.get("transaction_id")

    if not all([transaction_id, transaction_id]):
        logger.error(f"[Kafka] Missing required fields in auth-reserve-result: {event}")
        return

    try:
        sagaOrchestrator = SagaOrchestrator.objects.get(id=transaction_id)
    except SagaOrchestrator.DoesNotExist:
        logger.error(f"[Kafka] Purchase with id {transaction_id} not found")
        return

    if success:
        sagaOrchestrator.transaction_status = SagaOrchestrator.STATUS_CHOICES[0]
        sagaOrchestrator.save(update_fields=["transaction_status"])
        logger.info(f"[Kafka] Transaction {transaction_id} -> RESERVED")

        send_kafka_message("inventory-add", {
            "user_id": sagaOrchestrator.user_id,
            "product_id": sagaOrchestrator.item.id,
            "transaction_id": transaction_id
        })
        logger.info(f"[Kafka] Sent inventory-add for transaction {transaction_id}")
    else:
        sagaOrchestrator.transaction_status = SagaOrchestrator.STATUS_CHOICES[2]
        sagaOrchestrator.save(update_fields=["transaction_status"])
        logger.warning(f"[Kafka] sagaOrchestrator {transaction_id} -> DECLINED")


def handle_inventory_result(event: dict):
    """
    Обрабатывает результат добавления товара в инвентарь.
    """
    success = event.get("success")
    transaction_id = event.get("transaction_id")

    if not all(transaction_id):
        logger.error(f"[Kafka] Missing required fields in inventory-result: {event}")
        return

    try:
        sagaOrchestrator = SagaOrchestrator.objects.get(id=transaction_id)
    except SagaOrchestrator.DoesNotExist:
        logger.error(f"[Kafka] Transaction with id {transaction_id} not found")
        return

    if success:
        send_kafka_message("auth-commit", {
            "transaction_id": transaction_id
        })
        logger.info(f"[Kafka] Sent auth-commit for transaction {transaction_id}")
    else:
        sagaOrchestrator.transaction_status = SagaOrchestrator.STATUS_CHOICES[2]
        sagaOrchestrator.save(update_fields=["transaction_status"])
        logger.warning(f"[Kafka] Transaction {transaction_id} -> FAILED (inventory error)")


def handle_auth_commit_result(event: dict):
    """
    Обрабатывает результат финального списания средств.
    """
    transaction_id = event.get("transaction_id")
    success = event.get("success")

    if not transaction_id:
        logger.error(f"[Kafka] Missing transaction_id in auth-commit-result: {event}")
        return

    try:
        sagaOrchestrator = SagaOrchestrator.objects.get(id=transaction_id)
    except SagaOrchestrator.DoesNotExist:
        logger.error(f"[Kafka] Purchase with id {transaction_id} not found")
        return

    if success:
        sagaOrchestrator.transaction_status = SagaOrchestrator.STATUS_CHOICES[1]
        logger.info(f"[Kafka] Transaction {transaction_id} -> COMPLETED")
    else:
        sagaOrchestrator.transaction_status = SagaOrchestrator.STATUS_CHOICES[2]
        logger.warning(f"[Kafka] Transaction {transaction_id} -> FAILED (auth commit)")

    sagaOrchestrator.save(update_fields=["status"])


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