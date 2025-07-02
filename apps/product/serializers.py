from rest_framework import serializers
from .models import Product
from apps.chest.models import Chest
from apps.promotion.models import Promotion


class PromotionSerializer(serializers.ModelSerializer):
	class Meta:
		model = Promotion
		fields = ['id', 'name']


class ChestSerializer(serializers.ModelSerializer):
	class Meta:
		model = Chest
		fields = ['id', 'name']


class ProductSerializer(serializers.ModelSerializer):
	chest = ChestSerializer(read_only=True, allow_null=True)
	promotion = PromotionSerializer(read_only=True)
	is_available = serializers.SerializerMethodField()

	class Meta:
		model = Product
		fields = [
			'id',
			'name',
			'description',
			'currency_type',
			'cost',
			'promotion',
			'chest',
			'is_available'
		]

	def get_is_available(self, obj):
		"""Определяем доступность продукта"""
		return obj.cost is not None and obj.chest is None


class ProductPurchaseSerializer(serializers.Serializer):
	product_id = serializers.IntegerField()

	def validate_product_id(self, value):
		try:
			product = Product.objects.get(pk=value)
			if not (product.cost is not None and product.chest is None):
				raise serializers.ValidationError("This product is not available for purchase")
			return value
		except Product.DoesNotExist:
			raise serializers.ValidationError("Product does not exist")
