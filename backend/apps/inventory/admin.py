from django.contrib import admin

from .models import InventoryItem


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ["user", "ingredient", "created_at"]
    list_select_related = ["user", "ingredient"]
    search_fields = ["ingredient__name"]
    raw_id_fields = ["user", "ingredient"]
