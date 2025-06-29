from django.contrib import admin

from apps.chest.models import Chest


@admin.register(Chest)
class ChestAdmin(admin.ModelAdmin):
    list_display = ("id", "owner", "gold", "name", "promotion", "item_probability", "currency_type", "cost")
    list_filter = ("cost", "promotion",)
    search_fields = ("owner", "cost", )
