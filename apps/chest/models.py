from django.db import models
from apps.promotion.models import Promotion


class Chest(models.Model):
	gold = models.CharField(max_length=255)
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
	daily_purchase_limit = models.PositiveIntegerField(
		null=True,
		blank=True,
		help_text="Максимальное количество покупок в день для этого сундука (null — без лимита)"
	)
	reward_distribution = models.JSONField(
		null=True,
		blank=True,
		default=dict,
		help_text="Распределение вероятностей наград в сундуке"
	)

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
			chest_id=self.id,
			status__in=['PENDING', 'COMPLETED'],
			created_at__gte=start_of_day,
			created_at__lt=end_of_day
		).count()

		return purchase_count < self.daily_purchase_limit
