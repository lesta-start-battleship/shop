from django.contrib import admin
from .models import Purchase


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ("id", "owner", "item_id", "chest_id", "promotion_id", "date")
    list_filter = ("date",)
    search_fields = ("owner",)
