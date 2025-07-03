from django.core.exceptions import ValidationError
from apps.purchase.models import Purchase
from apps.product.models import Product
from apps.chest.models import Chest
from apps.promotion.models import Promotion
from kafka.producer import send_chest_promo_purchase_kafka_event


def create_purchase(owner_id: int, item_id=None, chest_id=None, promotion_id=None, quantity=1) -> Purchase:
    if quantity <= 0:
        raise ValidationError("Количество должно быть положительным.")

    item = chest = promotion = None

    if item_id:
        if chest_id:
            raise ValidationError("Нельзя одновременно указать и item, и chest.")
        item = Product.objects.get(id=item_id)
        if item.cost <= 0:
            raise ValidationError("Цена предмета должна быть положительной.")

    elif chest_id:
        chest = Chest.objects.get(id=chest_id)
        if chest.cost <= 0:
            raise ValidationError("Цена сундука должна быть положительной.")
    else:
        raise ValidationError("Должен быть указан либо item_id, либо chest_id.")

    if promotion_id:
        promotion = Promotion.objects.get(id=promotion_id)
        if promotion.price <= 0:
            raise ValidationError("Цена акции должна быть положительной.")

    purchase = Purchase.objects.create(
        owner=owner_id,
        item=item,
        chest=chest,
        promotion=promotion,
        quantity=quantity,
    )

    # Если куплен сундук в рамках акции — отправляем событие в Kafka
    if chest and promotion:
        send_chest_promo_purchase_kafka_event(owner_id, quantity)

    return purchase
