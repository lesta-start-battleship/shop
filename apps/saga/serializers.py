from rest_framework import serializers

from apps.chest.models import Chest
from apps.product.models import Product


class PurchaseRequestSerializer(serializers.Serializer):
	product_type = serializers.ChoiceField(
		choices=[('product', 'Product'), ('chest', 'Chest')]
	)
	product_id = serializers.IntegerField(min_value=1)
	quantity = serializers.IntegerField(min_value=1, default=1)

	def validate(self, data):
		# Проверка существования продукта/сундука
		if data['product_type'] == 'product':
			if not Product.objects.filter(id=data['product_id']).exists():
				raise serializers.ValidationError("Product not found")
		elif data['product_type'] == 'chest':
			if not Chest.objects.filter(id=data['product_id']).exists():
				raise serializers.ValidationError("Chest not found")
		return data