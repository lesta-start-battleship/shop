from celery import shared_task
from django.utils.timezone import now
from apps.promotion.models import Promotion
from django.db.models import F 

@shared_task
def delete_expired_promotions():
    current_time = now()
    expired_promos = Promotion.objects.filter(
        start_time__lte=current_time - F('duration')
    )

    count = expired_promos.count()
    expired_promos.delete()
    return f"Deleted {count} expired promotions"