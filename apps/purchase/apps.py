from django.apps import AppConfig
from rest_framework import serializers
from .models import Purchase

class PurchaseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.purchase'

class PurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Purchase
        fields = '__all__'

    def validate(self, data):
        targets = [data.get('item_id'), data.get('chest_id'), data.get('promotion_id')]
        if sum(x is not None for x in targets) != 1:
            raise serializers.ValidationError("Ровно одно из полей item_id, chest_id, promotion_id должно быть заполнено.")
        return data