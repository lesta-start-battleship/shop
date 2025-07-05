from rest_framework import serializers
from .models import Purchase

class PurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Purchase
        fields = '__all__'

    def validate(self, data):
        item = data.get('item')
        chest = data.get('chest')

        if (item is None and chest is None) or (item and chest):
            raise serializers.ValidationError("Ровно одно из полей item или chest должно быть заполнено.")

        if data.get("quantity", 1) <= 0:
            raise serializers.ValidationError("Количество должно быть положительным.")

        if item and item.cost <= 0:
            raise serializers.ValidationError("Цена предмета должна быть положительной.")
        if chest and chest.cost <= 0:
            raise serializers.ValidationError("Цена сундука должна быть положительной.")

        return data



