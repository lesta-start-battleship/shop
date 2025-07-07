from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.product.models import Product as Item
from apps.chest.models import Chest
from apps.promotion.models import Promotion


class Purchase(models.Model):
    """
    Покупка: предмета или сундука, с возможной привязкой к акции.
    """
    owner = models.IntegerField()  # UID пользователя

    item = models.ForeignKey(Item, null=True, blank=True, on_delete=models.SET_NULL, related_name='purchase_item')
    chest = models.ForeignKey(Chest, null=True, blank=True, on_delete=models.SET_NULL, related_name='purchase_chest')
    promotion = models.ForeignKey(Promotion, null=True, blank=True, on_delete=models.SET_NULL, related_name='purchase_promo')

    quantity = models.PositiveIntegerField(default=1)
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        base = f"Purchase #{self.id} by UID {self.owner}: "
        if self.item:
            return base + f"item #{self.item_id}, qty {self.quantity}"
        if self.chest:
            return base + f"chest #{self.chest_id}, qty {self.quantity}"
        return base + "unknown"

    def clean(self):
        if (self.item is None and self.chest is None) or (self.item and self.chest):
            raise ValidationError("Ровно одно из полей item или chest должно быть заполнено.")
        if self.quantity <= 0:
            raise ValidationError("Количество должно быть положительным.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
