import uuid
from django.db import models


class Transaction(models.Model):
	STATUS_CHOICES = [
		('pending', 'Pending'),
		('completed', 'Completed'),
		('compensating', 'Compensating'),
		('compensated', 'Compensated'),
		('compensation_failed', 'Compensation Failed'),
		('failed', 'Failed'),
	]

	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	user_id = models.IntegerField()
	item_id = models.IntegerField(null=True, blank=True)
	chest_id = models.IntegerField(null=True, blank=True)
	cost = models.IntegerField()
	currency_type = models.CharField(max_length=255)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
	created_at = models.DateTimeField(auto_now_add=True)
	promotion_id = models.IntegerField(null=True, blank=True)
	inventory_data = models.JSONField(
		null=True,
		blank=True,
		default=dict
	)
	error_message = models.TextField(null=True, blank=True)
	token = models.CharField(max_length=1000, null=True, blank=True)
