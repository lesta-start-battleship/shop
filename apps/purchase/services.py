from django.core.exceptions import ValidationError
from apps.purchase.models import Purchase
from apps.product.models import Product
from apps.chest.models import Chest
from apps.promotion.models import Promotion


def create_purchase(owner_id: int, item_id,promotion_id=None, quantity=1) -> Purchase:
    item = Product.objects.get(item_id=item_id)
    if item is None:
        chest = Chest.objects.get(item_id=item_id)
    if promotion_id:
        promotion = Promotion.objects.get(id=promotion_id)

    purchase = Purchase.objects.create(
        owner=owner_id,
        item=item,
        chest=chest,
        promotion=promotion,
        quantity=quantity,
    )
    return purchase
