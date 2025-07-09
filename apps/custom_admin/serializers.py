from rest_framework import serializers
from apps.chest.models import Chest
from apps.chest.serializers import ChestSerializer
from apps.product.models import Product
from apps.product.serializers import ProductPromotionSerializer
from apps.promotion.serializers import BasePromotionSerializer


class ProductDetailSerializer(serializers.ModelSerializer):
	class Meta:
		model = Product
		fields = ['item_id', 'name', 'description']


class ProductIdSerializer(serializers.PrimaryKeyRelatedField):
	def get_queryset(self):
		return Product.objects.all()

	def to_internal_value(self, data):
		try:
			product = Product.objects.get(item_id=data)
			return super().to_internal_value(product.id)
		except Product.DoesNotExist:
			raise serializers.ValidationError(f"Product with item_id={data} does not exist")
		except (TypeError, ValueError):
			raise serializers.ValidationError("Incorrect type. Expected item_id value.")

	def to_representation(self, value):
		return ProductDetailSerializer(value, context=self.context).data


class AdminChestSerializer(serializers.ModelSerializer):
	products = ProductDetailSerializer(
		many=True,
		source='product',
		read_only=True
	)

	special_products = ProductDetailSerializer(
		many=True,
		read_only=True
	)

	product_ids = ProductIdSerializer(
		many=True,
		write_only=True,
		source='product',
		required=False
	)

	special_products_ids = ProductIdSerializer(
		many=True,
		write_only=True,
		source='special_products',
		required=False
	)

	class Meta:
		model = Chest
		fields = [
			"item_id", "name", "gold", "promotion", "item_probability",
			"currency_type", "cost", "experience", "products", 'product_ids', 'special_products',
			'special_products_ids',
			"daily_purchase_limit", "reward_distribution"
		]
		extra_kwargs = {
			'item_id': {'read_only': True}
		}

		def create(self, validated_data):
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
	products = ProductPromotionSerializer(many=True, read_only=True)

	class Meta(BasePromotionSerializer.Meta):
		fields = BasePromotionSerializer.Meta.fields + ["chests", "products"]
