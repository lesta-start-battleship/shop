# apps/product/models.py
from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    currency_type = models.CharField(max_length=255, blank=True, null=True)
    cost = models.IntegerField(blank=True, null=True)
    promotion = models.ForeignKey(
        "promotion.Promotion", 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True, 
        related_name='products'
    )
    chest = models.ForeignKey(
        "chest.Chest", 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True, 
        related_name='products_in_chest'
    )

    def __str__(self):
        return self.name

    @property
    def is_available(self):
        """Товар доступен для покупки если:
        - Имеет цену (cost не None)
        - Не привязан к сундуку
        """
        return self.cost is not None and self.chest is None