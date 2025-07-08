from rest_framework import serializers
from apps.chest.models import Chest
from apps.chest.serializers import ChestSerializer
from apps.product.models import Product
from apps.product.serializers import ItemPromotionSerializer
from apps.promotion.serializers import BasePromotionSerializer



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

	special_products = ProductDetailSerializer(
		many=True,
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

	special_products_ids = ProductIdSerializer(
		queryset=Product.objects.all(),
		many=True,
		write_only=True,
		source='special_products',
		required=False
	)

	class Meta:
		model = Chest
		fields = [
			"item_id", "name", "gold", "promotion", "item_probability",
			"currency_type", "cost", "experience", "products", 'product_ids', 'special_products', 'special_products_ids',
			"daily_purchase_limit", "reward_distribution"
		]
		extra_kwargs = {
			'item_id': {'read_only': True}
		}

	def create(self, validated_data):
		# Обрабатываем продукты (уже как ID через product_ids)
		products = validated_data.pop('product', [])
		special_products = validated_data.pop('special_products', [])

		chest = Chest.objects.create(**validated_data)

		if products:
			chest.product.set(products)
		if special_products:
			chest.special_products.set(special_products)

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


class AdminPromotionSerializer(BasePromotionSerializer):
    chests = ChestSerializer(many=True, read_only=True)
    products = ItemPromotionSerializer(many=True, read_only=True)
    
    class Meta(BasePromotionSerializer.Meta):
        fields = BasePromotionSerializer.Meta.fields + ["chests", "products"]
