from rest_framework import serializers

from apps.chest.models import Chest


class ChestSerializer(serializers.ModelSerializer):
    products = serializers.SerializerMethodField()
    special_products = serializers.SerializerMethodField()

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
            "products",
            "special_products"
        ]

    def get_products(self, obj):
        from apps.product.serializers import ProductSerializer
        return ProductSerializer(obj.product.all(), many=True, context=self.context).data

    def get_special_products(self, obj):
        from apps.product.serializers import ProductSerializer
        return ProductSerializer(obj.special_products.all(), many=True, context=self.context).data


class ChestOpenSerializer(serializers.Serializer):
    item_id = serializers.IntegerField(required=True)
    amount = serializers.IntegerField(required=True)
