from django.db import models

from apps.chest.models import Chest
from apps.promotion.models import Promotion


class Product(models.Model):
	name = models.CharField(max_length=255)
	description = models.TextField()
	currency_type = models.CharField(max_length=255)
	cost = models.IntegerField()
	promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, blank=True, null=True)
	chest = models.ForeignKey(Chest, on_delete=models.CASCADE, blank=True, null=True, related_name='product')

	def __str__(self):
		return self.name
