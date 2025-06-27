def promotion_has_ended(promotion):
    from django.utils.timezone import now
    return now() > (promotion.start_time + promotion.duration)

def compensate_unopened_chests(promotion):
    pass