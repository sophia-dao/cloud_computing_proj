"""
Inventory API serializers. Response shape follows docs/api-design.md section 18.
"""

from rest_framework import serializers

from apps.ingredients.models import Ingredient

from .models import InventoryItem


class IngredientSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ["id", "name"]


class InventoryItemSerializer(serializers.ModelSerializer):
    """
    Read:  {"id": 101, "ingredient": {"id": 3, "name": "Egg"}}
    Write: {"ingredient_id": 3}

    `id` is the inventory item's own ID (used for DELETE). `ingredient.id` is
    the canonical ingredient's ID. There is no user field at all: the owner
    always comes from the logged-in user, so a user_id sent by the client is ignored.
    """

    ingredient = IngredientSummarySerializer(read_only=True)
    # Must reference an existing canonical Ingredient. An unknown ID is a
    # validation error and never creates a new Ingredient.
    ingredient_id = serializers.PrimaryKeyRelatedField(
        source="ingredient", queryset=Ingredient.objects.all(), write_only=True
    )

    class Meta:
        model = InventoryItem
        fields = ["id", "ingredient", "ingredient_id"]
