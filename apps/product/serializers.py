from rest_framework import serializers
from .models import Product
from apps.chest.models import Chest
from apps.promotion.models import Promotion


class ProductPromotionSerializer(serializers.ModelSerializer):
	class Meta:
		model = Promotion
		fields = ['id', 'name']


class ProductSerializer(serializers.ModelSerializer):
	promotion = ProductPromotionSerializer(read_only=True)

	class Meta:
		model = Product
		fields = [
			'item_id',
			'name',
			'description',
			'currency_type',
			'cost',
			'promotion'
		]
