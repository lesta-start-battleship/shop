from rest_framework import serializers
from .models import Purchase

class PurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Purchase
        fields = '__all__'

    def validate(self, data):
        item = data.get('item')
        chest = data.get('chest')
        promotion = data.get('promotion')

        # Проверка: ровно одно из item и chest должно быть заполнено
        if (item is None and chest is None) or (item and chest):
            raise serializers.ValidationError(
                "Ровно одно из полей item или chest должно быть заполнено."
            )

        # Проверка цены у promotion (если указан)
        if promotion and promotion.price <= 0:
            raise serializers.ValidationError("Цена акции должна быть положительной.")

        # Проверка положительной цены у item/chest
        if item and item.cost <= 0:
            raise serializers.ValidationError("Цена предмета должна быть положительной.")
        if chest and chest.cost <= 0:
            raise serializers.ValidationError("Цена сундука должна быть положительной.")

        return data
