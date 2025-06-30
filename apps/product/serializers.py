from .models import Product
from rest_framework import serializers

from ..promotion.models import Promotion


class PromotionProduct(serializers.ModelSerializer):
	class Meta:
		model = Promotion
		fields = ['id', 'name']


class ProductSerializer(serializers.ModelSerializer):
	promotion = PromotionProduct(read_only=True)

	class Meta:
		model = Product
		fields = ['id', 'name', 'description', 'cost', 'promotion', 'chest']
