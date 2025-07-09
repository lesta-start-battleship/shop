from django.db import models

from apps.promotion.models import Promotion


class Product(models.Model):
	item_id = models.IntegerField(unique=True, help_text="ID предмета из инвентарной системы")
	name = models.CharField(max_length=255)
	description = models.TextField()
	currency_type = models.CharField(max_length=255, blank=True, null=True)
	cost = models.IntegerField(blank=True, null=True)
	promotion = models.ForeignKey(Promotion,
		on_delete=models.SET_NULL,
		blank=True,
		null=True,
		related_name='products'
	)
	daily_purchase_limit = models.PositiveIntegerField(
		null=True,
		blank=True,
		help_text="Максимальное количество покупок в день для этого предмета (null — без лимита)"
	)
	kind = models.CharField(max_length=50, blank=True, null=True, help_text="Тип предмета")

	def __str__(self):
		return f"{self.name} (ID: {self.item_id})"

	def check_daily_purchase_limit(self, user_id):
		if self.daily_purchase_limit is None:
			return True

		from datetime import datetime, timedelta
		from django.utils import timezone
		from apps.saga.models import Transaction

		start_of_day = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
		end_of_day = start_of_day + timedelta(days=1)

		purchase_count = Transaction.objects.filter(
			user_id=user_id,
			item_id=self.item_id,
			status__in=['PENDING', 'COMPLETED'],
			created_at__gte=start_of_day,
			created_at__lt=end_of_day
		).count()

		return purchase_count < self.daily_purchase_limit
