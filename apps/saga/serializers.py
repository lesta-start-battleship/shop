from rest_framework import serializers

from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
	class Meta:
		model = Transaction
		fields = ['id', 'user_id', 'item_id', 'cost', 'currency_type', 'status', 'created_at',
				  'promotion_id', 'inventory_data', 'error_message']
		read_only_fields = ('status', 'created_at')
