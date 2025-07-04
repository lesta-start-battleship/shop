from celery import shared_task
from django.utils import timezone
from .models import Promotion
from .services import compensate_promotion
import logging

logger = logging.getLogger(__name__)

@shared_task
def check_and_compensate_expired_promotions():
    logger.info("Started compensation check for expired promotions.")
    
    expired_promos = Promotion.objects.filter(end_date__lt=timezone.now(), compensation_done=False)
    
    for promo in expired_promos:
        logger.info(f"Processing compensation for Promotion ID: {promo.id} - {promo.name}")
        
        try:
            count = compensate_promotion(promo)
            logger.info(f"Successfully compensated {count} items for Promotion ID: {promo.id}")
        except Exception as e:
            logger.error(f"Error compensating Promotion ID {promo.id}: {str(e)}", exc_info=True)