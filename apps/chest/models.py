from django.db import models

from apps.promotion.models import Promotion


class Chest(models.Model):
    gold = models.CharField()
    name = models.CharField(max_length=128)
    promotion = models.ForeignKey(
        Promotion,
        on_delete=models.SET_NULL,
        null=True,
        related_name="chest_promotion",
        default=None,
        blank=True
    )
    item_probability = models.FloatField()
    currency_type = models.CharField(max_length=32)
    cost = models.IntegerField(default=1)
