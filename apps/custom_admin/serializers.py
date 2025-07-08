from rest_framework import serializers
from apps.chest.models import Chest
from apps.product.models import Product
from apps.promotion.models import Promotion


class ProductDetailSerializer(serializers.ModelSerializer):
	class Meta:
		model = Product
		fields = ['name', 'description']  # Только нужные поля


class AdminChestSerializer(serializers.ModelSerializer):
	products = ProductDetailSerializer(
		many=True,
		source='product',  # Используем related_name из модели Chest
		required=False
	)

	special_products = ProductDetailSerializer(
		many=True,
		source='product',  # Используем related_name из модели Chest
		required=False
	)

	class Meta:
		model = Chest
		fields = [
			"item_id", "name", "gold", "promotion", "item_probability",
			"currency_type", "cost", "experience", "products", 'special_products',
			"daily_purchase_limit", "reward_distribution"
		]
		extra_kwargs = {
			'item_id': {'read_only': True}
		}

	def create(self, validated_data):
		# Извлекаем данные продуктов (если есть)
		products_data = validated_data.pop('product', [])

		# Создаем сундук
		chest = Chest.objects.create(**validated_data)

		# Обрабатываем продукты
		if products_data:
			products = []
			for product_data in products_data:
				product, _ = Product.objects.get_or_create(
					name=product_data['name'],
					defaults={'description': product_data['description']}
				)
				products.append(product)
			chest.product.set(products)

		return chest


class AdminProductSerializer(serializers.ModelSerializer):
	class Meta:
		model = Product
		fields = ["id", 'item_id', 'name', 'description', 'currency_type', 'cost', 'promotion', 'daily_purchase_limit']

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
