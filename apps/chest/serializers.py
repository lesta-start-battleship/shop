from rest_framework import serializers

from apps.chest.models import Chest
from apps.product.models import Product


# class ChestProductSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Product
#         fields = ['id', 'name']
#
#
# class ChestSerializer(serializers.ModelSerializer):
#     products_in_chest = ChestProductSerializer(many=True, read_only=True)
#
#     class Meta:
#         model = Chest
#         fields = ['id', 'name', 'gold', 'promotion', 'item_probability', 'currency_type', 'cost', 'products_in_chest']


class ChestSerializer(serializers.ModelSerializer):
    products = serializers.SerializerMethodField()

    class Meta:
        model = Chest
        fields = [
            "id",
            "name",
            "gold",
            "promotion",
            "item_probability",
            "currency_type",
            "cost",
            "experience",
            "products"
        ]

    def get_products(self, obj):
        from apps.product.serializers import ProductSerializer  # Локальный импорт
        return ProductSerializer(obj.product.all(), many=True, context=self.context).data
