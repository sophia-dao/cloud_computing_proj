"""
Recommendation request/response serializers. Field names follow
docs/api-design.md section 20:

    {
      "ingredients": [3, 4, 5],          # or "use_saved_inventory": true
      "match_mode": "AVAILABLE_ONLY",    # or "PARTIAL_MATCH"
      "filters": {"tag_ids": [], "allergen_ids": []}
    }
"""

from collections.abc import Mapping

from rest_framework import serializers

from apps.ingredients.models import Ingredient
from apps.recipes.filters import MAX_VALUES_PER_FILTER
from apps.recipes.models import Recipe, Tag
from apps.users.models import Allergen

from .services import MATCH_MODES

# Caps the ingredient list so an oversized request gets a clear 400 instead
# of an enormous database query. Filter lists use recipe search's limit.
MAX_INGREDIENTS = 500

# Point anyone using older/alternate field names at the documented ones.
RENAMED_FIELDS = {
    "ingredient_ids": "ingredients",
    "mode": "match_mode",
    "tag_ids": "filters.tag_ids",
    "allergen_ids": "filters.allergen_ids",
}


class RejectUnknownFieldsMixin:
    """Return 400 for unexpected fields (such as user_id) instead of silently ignoring them."""

    def to_internal_value(self, data):
        if isinstance(data, Mapping):
            unknown = sorted(set(data) - set(self.fields))
            if unknown:
                errors = {}
                for name in unknown:
                    hint = RENAMED_FIELDS.get(name)
                    errors[name] = [f"Unknown field. Did you mean '{hint}'?" if hint else "Unknown field."]
                raise serializers.ValidationError(errors)
        return super().to_internal_value(data)


def id_list_field(max_length, **kwargs):
    return serializers.ListField(
        child=serializers.IntegerField(min_value=1), max_length=max_length, **kwargs
    )


def validate_existing_ids(model, ids, label):
    """Remove duplicates and confirm every ID exists, using one query."""
    unique_ids = sorted(set(ids))
    if not unique_ids:
        return []
    found = set(model.objects.filter(pk__in=unique_ids).values_list("pk", flat=True))
    missing = [pk for pk in unique_ids if pk not in found]
    if missing:
        raise serializers.ValidationError(f"Unknown {label} ID(s): {missing}")
    return unique_ids


class RecommendationFiltersSerializer(RejectUnknownFieldsMixin, serializers.Serializer):
    tag_ids = id_list_field(MAX_VALUES_PER_FILTER, required=False, default=list)
    allergen_ids = id_list_field(MAX_VALUES_PER_FILTER, required=False, default=list)

    def validate_tag_ids(self, value):
        return validate_existing_ids(Tag, value, "tag")

    def validate_allergen_ids(self, value):
        return validate_existing_ids(Allergen, value, "allergen")


class RecommendationRequestSerializer(RejectUnknownFieldsMixin, serializers.Serializer):
    ingredients = id_list_field(MAX_INGREDIENTS, required=False)
    match_mode = serializers.ChoiceField(choices=MATCH_MODES)
    use_saved_inventory = serializers.BooleanField(required=False, default=False)
    filters = RecommendationFiltersSerializer(required=False)

    def validate_ingredients(self, value):
        # Duplicates are dropped here, so they can't inflate counts or scores.
        return validate_existing_ids(Ingredient, value, "ingredient")

    def validate(self, attrs):
        has_ingredients = "ingredients" in attrs
        if attrs["use_saved_inventory"] and has_ingredients:
            raise serializers.ValidationError(
                {"ingredients": ["Send either ingredients or use_saved_inventory, not both."]}
            )
        if not attrs["use_saved_inventory"] and not has_ingredients:
            raise serializers.ValidationError(
                {"ingredients": ["This field is required unless use_saved_inventory is true."]}
            )
        attrs.setdefault("filters", {"tag_ids": [], "allergen_ids": []})
        return attrs


# ---------- Response ----------

class IngredientSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ["id", "name"]


class RecipeSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ["id", "name", "image"]


class RecommendationResultSerializer(serializers.Serializer):
    recipe = RecipeSummarySerializer()
    match_score = serializers.FloatField()
    available_ingredients = IngredientSummarySerializer(many=True)
    missing_ingredients = IngredientSummarySerializer(many=True)
    optional_missing_ingredients = IngredientSummarySerializer(many=True)
