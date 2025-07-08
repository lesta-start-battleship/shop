from rest_framework import serializers
from apps.chest.models import Chest
from apps.product.models import Product
from apps.promotion.models import Promotion


class AdminChestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chest
        fields = ['id', 'name', 'gold', 'item_probability', 'cost', 'daily_purchase_limit', 'currency_type',
                  'promotion', 'experience', 'product', 'special_products', 'reward_distribution']


class AdminProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'currency_type', 'cost', 'promotion', 'daily_purchase_limit']

    def validate_name(self, value):
        if self.instance and value != self.instance.name:
            raise serializers.ValidationError("Поле 'name' нельзя изменять.")
        return value

    def validate_description(self, value):
        if self.instance and value != self.instance.description:
            raise serializers.ValidationError("Поле 'description' нельзя изменять.")
        return value

    def validate_currency_type(self, value):
        if self.instance and value != self.instance.currency_type:
            raise serializers.ValidationError("Поле 'currency_type' нельзя изменять.")
        return value

    def create(self, validated_data):
        raise serializers.ValidationError("Создание новых предметов запрещено.")


class AdminPromotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promotion
        fields = ['id', 'name', 'description', 'start_date', 'duration', 'manually_disabled', 'compensation_done']
