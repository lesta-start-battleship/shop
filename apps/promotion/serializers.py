from rest_framework import serializers
from .models import Promotion
from apps.chest.serializers import ChestSerializer


class PromotionSerializer(serializers.ModelSerializer):
    end_time = serializers.SerializerMethodField()
    items_count = serializers.SerializerMethodField()
    chests = ChestSerializer(many=True)

    class Meta:
        model = Promotion
        fields = ["id", "name", "start_time", "duration", "end_time", "price", "chests", "items_count"]

    def get_end_time(self, obj):
        return obj.start_time + obj.duration

    def get_items_count(self, obj):
        return obj.items.count() + obj.chests.count()
