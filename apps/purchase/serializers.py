from rest_framework import serializers
from .models import Purchase


class PurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Purchase
        fields = '__all__'

    def validate(self, data):
        targets = [data.get('item'), data.get('chest'), data.get('promotion')]
        if sum(x is not None for x in targets) != 1:
            raise serializers.ValidationError(
                "Ровно одно из полей item, chest или promotion должно быть заполнено."
            )
        return data
