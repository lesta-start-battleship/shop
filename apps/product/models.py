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
	daily_purchase_limit = models.PositiveIntegerField(
		null=True,
		blank=True,
		help_text="Максимальное количество покупок в день для этого предмета (null — без лимита)"
	)

	def __str__(self):
		return self.name

	@property
	def is_available(self):
		return self.cost is not None

	def check_daily_purchase_limit(self, user_id):
		if self.daily_purchase_limit is None:
			return True  # Нет индивидуального лимита

		from datetime import datetime, timedelta
		from django.utils import timezone
		from apps.saga.models import Transaction

		start_of_day = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
		end_of_day = start_of_day + timedelta(days=1)

		purchase_count = Transaction.objects.filter(
			user_id=user_id,
			product_id=self.id,
			status__in=['PENDING', 'COMPLETED'],
			created_at__gte=start_of_day,
			created_at__lt=end_of_day
		).count()

		return purchase_count < self.daily_purchase_limit
