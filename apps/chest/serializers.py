from rest_framework import serializers
from .models import Chest
from apps.product.models import Product


class ProductChestSerializer(serializers.ModelSerializer):
	class Meta:
		model = Product
		fields = ['id', 'name', 'cost']


class ChestListSerializer(serializers.ModelSerializer):
	product = ProductChestSerializer(many=True)

	class Meta:
		model = Chest
		fields = ['id', 'name', 'gold', 'item_probability', 'currency_type', 'cost', 'promotion', 'product']
