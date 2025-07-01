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

        if (item is None and chest is None) or (item is not None and chest is not None):
            raise serializers.ValidationError(
                "Ровно одно из полей item или chest должно быть заполнено."
            )

        if promotion and promotion.price <= 0:
            raise serializers.ValidationError(
                "Цена акции должна быть положительной."
            )
        return data
