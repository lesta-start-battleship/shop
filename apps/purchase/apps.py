from django.apps import AppConfig
from .models import Purchase

class PurchaseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.purchase'

def check_promotion_limit(user_id: int, promotion_id: int, max_quantity: int) -> bool:
    """
    Проверяет, не превышен ли лимит покупок у пользователя для данной акции.
    """
    count = Purchase.objects.filter(
        owner=user_id,
        promotion_id=promotion_id
    ).count()
    return count < max_quantity  # True = можно купить