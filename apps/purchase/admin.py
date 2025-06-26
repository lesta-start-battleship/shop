from django.contrib import admin
from .models import Purchase

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ("id", "owner", "item", "chest", "promotion", "created_at")
    search_fields = ("owner",)
    list_filter = ("created_at",)
    ordering = ("-created_at",)
