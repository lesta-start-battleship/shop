from rest_framework import serializers

from apps.chest.models import Chest


class ChestSerializer(serializers.ModelSerializer):

    class Meta:
        model = Chest
        fields = ["id", "name", "gold", "promotion", "item_probability", "currency_type", "cost"]