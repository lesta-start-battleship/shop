import uuid
from apps.purchase.models import Purchase, TransactionStatus
from kafka.producer import send_kafka_message
from apps.product.models import Product

def start_product_purchase(user_id: int, product_id: int) -> Purchase:
    product = Product.objects.get(id=product_id)

    purchase = Purchase.objects.create(
        owner=user_id,
        item=product,
        quantity=1,
        transaction_status=TransactionStatus.PENDING
    )

    send_kafka_message("auth-reserve", {
        "user_id": user_id,
        "transaction_id": f"purchase-{purchase.id}",
        "cost": product.cost,
        "purchase_id": purchase.id
    })

    return purchase


def check_promotion_limit(user_id: int, promotion_id: int, max_quantity: int) -> bool:
    """
    Проверяет, не превышен ли лимит покупок у пользователя для данной акции.

    :param user_id: UID пользователя из заголовка X-User-ID
    :param promotion_id: ID акции
    :param max_quantity: максимальное количество покупок по акции
    :return: True, если покупка разрешена (лимит не превышен), иначе False
    """
    count = Purchase.objects.filter(
        owner=user_id,
        promotion_id=promotion_id
    ).count()
    return count < max_quantity
