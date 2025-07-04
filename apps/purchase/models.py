from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.product.models import Product as Item
from apps.chest.models import Chest
from apps.promotion.models import Promotion


class Purchase(models.Model):
    """
    Покупка: сундука, предмета или акции.
    """
    owner = models.IntegerField()  # UID пользователя

    item = models.ForeignKey(Item, null=True, blank=True, on_delete=models.SET_NULL, related_name='purchase_item')
    chest = models.ForeignKey(Chest, null=True, blank=True, on_delete=models.SET_NULL, related_name='purchase_chest')
    promotion = models.ForeignKey(Promotion, null=True, blank=True, on_delete=models.SET_NULL, related_name='purchase_promo')

    quantity = models.PositiveIntegerField(default=1)  # кол-во купленных сундуков/предметов/акций

    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        if self.item:
            return f"Purchase #{self.id} by UID {self.owner}: item #{self.item_id}, qty {self.quantity}"
        elif self.chest:
            return f"Purchase #{self.id} by UID {self.owner}: chest #{self.chest_id}, qty {self.quantity}"
        elif self.promotion:
            return f"Purchase #{self.id} by UID {self.owner}: promotion #{self.promotion_id}, qty {self.quantity}"
        return f"Purchase #{self.id} by UID {self.owner}: unknown"

    def clean(self):
        # Проверяем, что заполнено ровно одно из item или chest
        if (self.item is None and self.chest is None) or (self.item is not None and self.chest is not None):
            raise ValidationError("Ровно одно из полей item или chest должно быть заполнено.")

        # Проверка положительной цены
        if self.item and self.item.cost <= 0 or \
                self.chest and self.chest.cost <= 0 or \
                self.promotion and self.promotion.price <= 0:
            raise ValidationError("Цена должна быть положительной.")

        # Проверка количества
        if self.quantity <= 0:
            raise ValidationError("Количество должно быть положительным.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)