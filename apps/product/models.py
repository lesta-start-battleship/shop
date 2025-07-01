from django.db import models
import promotion, chest


class Product(models.Model):
	name = models.CharField(max_length=255)
	description = models.TextField()
	currency_type = models.CharField(max_length=255, blank=True, null=True)
	cost = models.IntegerField(blank=True, null=True)
	promotion = models.ForeignKey(promotion.Promotion, on_delete=models.CASCADE, blank=True, null=True, related_name='promotion_products')
	chest = models.ForeignKey(chest.Chest, on_delete=models.CASCADE, blank=True, null=True, related_name='chest_products')

	def __str__(self):
		return self.name
