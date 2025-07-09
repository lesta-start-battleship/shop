from django.core.exceptions import ValidationError
from apps.purchase.models import Purchase
from apps.product.models import Product
from apps.chest.models import Chest
from apps.promotion.models import Promotion


def create_purchase(owner_id: int, item_id, promotion_id=None, quantity=1) -> Purchase:
	try:
		item = Product.objects.get(item_id=item_id)
		chest = None
	except Product.DoesNotExist:
		try:
			chest = Chest.objects.get(item_id=item_id)
			item = None
		except Chest.DoesNotExist:
			raise ValueError(f"No Product or Chest found with item_id={item_id}")

	promotion = None
	if promotion_id:
		try:
			promotion = Promotion.objects.get(id=promotion_id)
		except Promotion.DoesNotExist:
			raise ValueError(f"Promotion with id={promotion_id} not found")

	purchase = Purchase.objects.create(
		owner=owner_id,
		item=item,
		chest=chest,
		promotion=promotion,
		quantity=quantity,
	)
	return purchase
