from django.contrib import admin

from .models import Recipe, RecipeIngredient, Tag


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    raw_id_fields = ["ingredient"]


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ["name", "owner", "created_at"]
    list_select_related = ["owner"]
    search_fields = ["name"]
    list_filter = ["tags"]
    filter_horizontal = ["tags"]
    raw_id_fields = ["owner"]
    inlines = [RecipeIngredientInline]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "type"]
    list_filter = ["type"]
    search_fields = ["name"]
