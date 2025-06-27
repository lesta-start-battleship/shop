from rest_framework import serializers
from .models import Promotion

class PromotionSerializer(serializers.ModelSerializer):
    end_time = serializers.SerializerMethodField()
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = Promotion
        fields = ["id", "name", "start_time", "duration", "end_time", "price", "item_ids", "items_count"]

    def get_end_time(self, obj):
        return obj.start_time + obj.duration

    def get_items_count(self, obj):
        return len(obj.item_ids) if obj.item_ids else 0