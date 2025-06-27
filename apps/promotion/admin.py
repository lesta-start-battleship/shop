from django.contrib import admin

from apps.chest.models import Promotion


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "duration", "items", "cost", "quantity", )
    list_filter = ("name", "cost",)
    search_fields = ("name", "cost",)
