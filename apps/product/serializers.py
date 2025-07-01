# apps/product/serializers.py
from rest_framework import serializers
from .models import Product
from apps.promotion.serializers import PromotionSerializer


class ProductSerializer(serializers.ModelSerializer):
	promotion = PromotionSerializer(read_only=True)
	is_available = serializers.BooleanField(read_only=True)

	class Meta:
		model = Product
		fields = [
			'id',
			'name',
			'description',
			'currency_type',
			'cost',
			'promotion',
			'is_available'
		]


class ProductPurchaseSerializer(serializers.Serializer):
	product_id = serializers.IntegerField()
	quantity = serializers.IntegerField(default=1, min_value=1)

	def validate_product_id(self, value):
		try:
			product = Product.objects.get(pk=value)
			if not product.is_available:
				raise serializers.ValidationError("This product is not available for purchase")
			return value
		except Product.DoesNotExist:
			raise serializers.ValidationError("Product does not exist")
