from rest_framework import serializers
from .models import Promotion
from apps.chest.serializers import ChestSerializer
from apps.product.serializers import ItemPromotionSerializer


class PromotionSerializer(serializers.ModelSerializer):
    items_count = serializers.SerializerMethodField()
    chests = ChestSerializer(many=True, read_only=True)
    products = ItemPromotionSerializer(many=True, read_only=True)
    is_active = serializers.SerializerMethodField()
    end_date = serializers.SerializerMethodField()

    class Meta:
        model = Promotion
        fields = [
            "id",
            "name",
            "start_date",
            "end_date",
            "chests",
            "products",
            "items_count",
            "is_active"
        ]

    def get_items_count(self, obj):
        return obj.products.count() + obj.chests.count()

    def get_is_active(self, obj):
        return obj.is_active()
    
    def get_end_date(self, obj):
        return obj.end_date
