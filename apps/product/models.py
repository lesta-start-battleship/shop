from django.db import models

from apps.promotion.models import Promotion


class Product(models.Model):
	name = models.CharField(max_length=255)
	description = models.TextField()
	cost = models.IntegerField()
	promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, blank=True, null=True)
	owner = models.IntegerField(blank=True, null=True)
	chest = models.IntegerField(blank=True, null=True)

	def __str__(self):
		return self.name
