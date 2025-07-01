from django.db import models
from django.core.exceptions import ValidationError
from apps.chest.models import Chest
from apps.promotion.models import Promotion


class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    available = models.BooleanField(default=True)
    currency_type = models.CharField(max_length=255, blank=True, null=True)
    cost = models.PositiveIntegerField(blank=True, null=True, default=1)
    promotion = models.ForeignKey(
        Promotion, on_delete=models.CASCADE, blank=True, null=True, related_name='promotion_products'
    )
    chest = models.ForeignKey(
        Chest, on_delete=models.CASCADE, blank=True, null=True, related_name='chest_products'
    )

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if self.cost is not None and self.cost <= 0:
            raise ValidationError({"cost": "Стоимость должна быть положительным числом."})
