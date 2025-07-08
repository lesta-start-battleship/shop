from rest_framework import serializers
from .models import Product
from apps.chest.models import Chest
from apps.promotion.models import Promotion


class ItemPromotionSerializer(serializers.ModelSerializer):
	class Meta:
		model = Promotion
		fields = ['id', 'name']


class ItemSerializer(serializers.ModelSerializer):
	promotion = ItemPromotionSerializer(read_only=True)

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
