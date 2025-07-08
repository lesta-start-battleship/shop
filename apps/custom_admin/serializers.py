from rest_framework import serializers
from apps.chest.models import Chest
from apps.product.models import Product
from apps.promotion.models import Promotion


class ProductDetailSerializer(serializers.ModelSerializer):
	class Meta:
		model = Product
		fields = ['id', 'name', 'description']  # Полные данные для чтения


class ProductIdSerializer(serializers.PrimaryKeyRelatedField):
	def to_internal_value(self, data):
		# Принимаем только ID продукта
		return super().to_internal_value(data)

	def to_representation(self, value):
		# При отображении используем полный сериализатор
		return ProductDetailSerializer(value, context=self.context).data


class AdminChestSerializer(serializers.ModelSerializer):
	# Для GET запросов - полные данные
	products = ProductDetailSerializer(
		many=True,
		source='product',
		read_only=True
	)

	# Для записи - только ID продуктов
	product_ids = ProductIdSerializer(
		queryset=Product.objects.all(),
		many=True,
		write_only=True,
		source='product',
		required=False
	)

	class Meta:
		model = Chest
		fields = [
			"item_id", "name", "gold", "promotion", "item_probability",
			"currency_type", "cost", "experience", "products", "product_ids",
			"daily_purchase_limit", "reward_distribution"
		]
		extra_kwargs = {
			'item_id': {'read_only': True}
		}

	def create(self, validated_data):
		# Обрабатываем продукты (уже как ID через product_ids)
		products = validated_data.pop('product', [])
		chest = Chest.objects.create(**validated_data)

		if products:
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
