from rest_framework import serializers
from .models import Chest, ChestSettings
from apps.product.models import Product


class ProductSummarySerializer(serializers.ModelSerializer):
	class Meta:
		model = Product
		fields = ['name', 'description']


class ChestSerializer(serializers.ModelSerializer):
	products = serializers.SerializerMethodField()
	special_products = serializers.SerializerMethodField()

	class Meta:
		model = Chest
		fields = [
			"item_id",
			"name",
			"gold",
			"promotion",
			"item_probability",
			"currency_type",
			"cost",
			"experience",
			"products",
			"special_products"
		]

	def get_products(self, obj):
		return ProductSummarySerializer(obj.product.all(), many=True, context=self.context).data

	def get_special_products(self, obj):
		return ProductSummarySerializer(obj.special_products.all(), many=True, context=self.context).data


class ChestOpenSerializer(serializers.Serializer):
	item_id = serializers.IntegerField(required=True)
	amount = serializers.IntegerField(required=True)


class ChestSettingsSerializer(serializers.ModelSerializer):

	class Meta:
		model = ChestSettings
		fields = '__all__'
