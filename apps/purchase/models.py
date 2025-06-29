from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

from kafka import send_chest_promo_purchase_event


class Purchase(models.Model):
    """
    Покупка: сундука, предмета или акции.
    """
    owner = models.IntegerField()  # UID пользователя
    item_id = models.IntegerField(null=True, blank=True)     # FK на Item (по id)
    chest_id = models.IntegerField(null=True, blank=True)     # FK на Chest (по id)
    promotion_id = models.IntegerField(null=True, blank=True) # FK на Promotion (по id)
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        if self.item_id:
            return f"Purchase #{self.id} by UID {self.owner}: item #{self.item_id}"
        elif self.chest_id:
            return f"Purchase #{self.id} by UID {self.owner}: chest #{self.chest_id}"
        elif self.promotion_id:
            return f"Purchase #{self.id} by UID {self.owner}: promotion #{self.promotion_id}"
        return f"Purchase #{self.id} by UID {self.owner}: unknown"

    def clean(self):
        filled = [self.item_id, self.chest_id, self.promotion_id]
        if sum(x is not None for x in filled) != 1:
            raise ValidationError("Ровно одно из полей item_id, chest_id или promotion_id должно быть заполнено.")

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and self.chest_id is not None and self.promotion_id is not None:
            # Это покупка сундука по акции
            send_chest_promo_purchase_event(self.owner)
