from rest_framework import serializers
from apps.chest.models import Chest
from apps.product.models import Product
from apps.promotion.models import Promotion


class AdminChestSerializer(serializers.ModelSerializer):
	products = serializers.PrimaryKeyRelatedField(
		queryset=Product.objects.all(),
		many=True,
		required=False
	)

	class Meta:
		model = Chest
		fields = [
			"item_id", "name", "gold", "promotion", "item_probability",
			"currency_type", "cost", "experience", "products",
			"daily_purchase_limit", "reward_distribution"
		]
		extra_kwargs = {
			'item_id': {'read_only': True}  # item_id нельзя задавать вручную
		}

	def create(self, validated_data):
		products = validated_data.pop('products', [])
		chest = Chest.objects.create(**validated_data)
		if products:
			chest.product.set(products)
		return chest


class AdminProductSerializer(serializers.ModelSerializer):
	class Meta:
		model = Product
		fields = ['item_id', 'name', 'description', 'currency_type', 'cost', 'promotion', 'daily_purchase_limit']

	def validate_name(self, value):
		if self.instance and value != self.instance.name:
			raise serializers.ValidationError("Поле 'name' нельзя изменять.")
		return value

	def validate_description(self, value):
		if self.instance and value != self.instance.description:
			raise serializers.ValidationError("Поле 'description' нельзя изменять.")
		return value

	def create(self, validated_data):
		raise serializers.ValidationError("Создание новых предметов запрещено.")


class AdminPromotionSerializer(serializers.ModelSerializer):
	class Meta:
		model = Promotion
		fields = ['id', 'name', 'description', 'start_date', 'duration', 'manually_disabled', 'compensation_done']
