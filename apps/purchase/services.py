from apps.purchase.models import Purchase

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
