from rest_framework import serializers
from apps.chest.models import Chest
from apps.product.models import Product


class AdminChestSerializer(serializers.ModelSerializer):
	class Meta:
		model = Chest
		fields = ['id', 'name', 'gold', 'item_probability', 'cost', 'daily_purchase_limit', 'currency_type',
				  'promotion']


class AdminProductSerializer(serializers.ModelSerializer):
	class Meta:
		model = Product
		fields = ['id', 'name', 'description', 'currency_type', 'cost', 'promotion', 'chest', 'daily_purchase_limit']

	def validate_name(self, value):
		if self.instance and value != self.instance.name:
			raise serializers.ValidationError("Поле 'name' нельзя изменять.")
		return value

	def validate_description(self, value):
		if self.instance and value != self.instance.description:
			raise serializers.ValidationError("Поле 'description' нельзя изменять.")
		return value

	def validate_currency_type(self, value):
		if self.instance and value != self.instance.currency_type:
			raise serializers.ValidationError("Поле 'currency_type' нельзя изменять.")
		return value

	def create(self, validated_data):
		raise serializers.ValidationError("Создание новых предметов запрещено.")


