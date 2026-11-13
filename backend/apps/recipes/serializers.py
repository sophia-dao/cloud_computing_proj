"""
Recipe API serializers. Response shapes follow docs/api-design.md section 19.
"""

import uuid

from django.db import transaction
from rest_framework import serializers

from apps.ingredients.models import Ingredient

from .models import Recipe, RecipeIngredient, SavedRecipe, Tag
from .services import normalize_recipe_name

# Same limit as the TheMealDB image import (backfill_recipe_images).
MAX_IMAGE_BYTES = 5_000_000
# Pillow format name -> file extension used when storing the upload.
ALLOWED_IMAGE_FORMATS = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}


class IngredientSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ["id", "name"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "type"]


# ---------- Read serializers ----------

class RecipeIngredientSerializer(serializers.ModelSerializer):
    ingredient = IngredientSummarySerializer(read_only=True)
    # Return quantity as a JSON number (DRF's default for decimals is a string).
    quantity = serializers.DecimalField(
        max_digits=8, decimal_places=3, coerce_to_string=False, read_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = ["ingredient", "quantity", "unit", "is_optional", "notes"]
        read_only_fields = fields


class RecipeListSerializer(serializers.ModelSerializer):
    """Smaller shape for GET /api/recipes/ (no ingredients or instructions)."""

    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Recipe
        fields = ["id", "name", "description", "image", "tags"]


class RecipeDetailSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()
    ingredients = RecipeIngredientSerializer(source="recipe_ingredients", many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Recipe
        fields = [
            "id",
            "owner",
            "name",
            "description",
            "preparation_time",
            "cooking_time",
            "ingredients",
            "tags",
            "instructions",
            "image",
        ]

    def get_owner(self, recipe):
        # owner_id is a column on the recipe row, so this costs no extra query.
        return {"id": recipe.owner_id} if recipe.owner_id else None


# ---------- Write serializers ----------

class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    # Must reference an existing canonical Ingredient; an unknown ID is a
    # validation error and never creates a new Ingredient.
    ingredient_id = serializers.PrimaryKeyRelatedField(
        source="ingredient", queryset=Ingredient.objects.all()
    )

    class Meta:
        model = RecipeIngredient
        fields = ["ingredient_id", "quantity", "unit", "is_optional", "notes"]

    def validate_unit(self, value):
        return value or None

    def validate_notes(self, value):
        return value or None


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Validates POST and PATCH bodies. Owner is never accepted from the client."""

    ingredients = RecipeIngredientWriteSerializer(many=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        source="tags", many=True, queryset=Tag.objects.all(), required=False
    )

    class Meta:
        model = Recipe
        fields = [
            "name",
            "description",
            "instructions",
            "preparation_time",
            "cooking_time",
            "ingredients",
            "tag_ids",
        ]

    def validate_name(self, value):
        # Stored normalized so the duplicate-name check can match exactly.
        return normalize_recipe_name(value)

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError("A recipe needs at least one ingredient.")
        ids = [item["ingredient"].pk for item in value]
        duplicates = sorted({pk for pk in ids if ids.count(pk) > 1})
        if duplicates:
            raise serializers.ValidationError(
                f"Each ingredient can appear only once per recipe. Duplicated ingredient IDs: {duplicates}"
            )
        return value

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop("ingredients")
        tags = validated_data.pop("tags", [])
        recipe = Recipe.objects.create(**validated_data)
        self._add_ingredients(recipe, ingredients)
        recipe.tags.set(tags)
        return recipe

    @transaction.atomic
    def update(self, recipe, validated_data):
        ingredients = validated_data.pop("ingredients", None)
        tags = validated_data.pop("tags", None)
        for field, value in validated_data.items():
            setattr(recipe, field, value)
        recipe.save()
        if ingredients is not None:
            # A submitted ingredient list replaces the old one.
            recipe.recipe_ingredients.all().delete()
            self._add_ingredients(recipe, ingredients)
        if tags is not None:
            recipe.tags.set(tags)
        return recipe

    def _add_ingredients(self, recipe, ingredients):
        RecipeIngredient.objects.bulk_create(
            [RecipeIngredient(recipe=recipe, **item) for item in ingredients]
        )

    def to_representation(self, recipe):
        # After a write, respond with the same shape as GET /api/recipes/{id}/.
        recipe = Recipe.objects.with_detail_relations().get(pk=recipe.pk)
        return RecipeDetailSerializer(recipe, context=self.context).data


# ---------- Recipe submission helpers (Issue #67) ----------

class RecipeNameCheckSerializer(serializers.Serializer):
    """Query parameters for GET /api/recipes/duplicates/."""

    name = serializers.CharField(max_length=200)


class RecipeMatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ["id", "name"]


class RecipeImageSerializer(serializers.Serializer):
    """Multipart body for POST /api/recipes/{id}/image/."""

    # Django's ImageField opens the file with Pillow, so anything that isn't
    # really an image is rejected even if its name ends in .jpg.
    image = serializers.ImageField()

    def validate_image(self, file):
        if file.size > MAX_IMAGE_BYTES:
            raise serializers.ValidationError(
                f"Images must be {MAX_IMAGE_BYTES // 1_000_000} MB or smaller."
            )
        image_format = getattr(getattr(file, "image", None), "format", None)
        if image_format not in ALLOWED_IMAGE_FORMATS:
            raise serializers.ValidationError("Upload a JPEG, PNG or WebP image.")
        # Store under a random name. The uploader's original filename is never
        # kept, and two uploads can't collide.
        file.name = f"{uuid.uuid4().hex}{ALLOWED_IMAGE_FORMATS[image_format]}"
        return file


# ---------- Saved recipes (Issue #14) ----------

class SavedRecipeSerializer(serializers.ModelSerializer):
    """One bookmark: {"id", "recipe": {list shape}, "created_at"}.

    Clients send {"recipe_id": 42}. The user always comes from authentication.
    """

    recipe = RecipeListSerializer(read_only=True)
    recipe_id = serializers.PrimaryKeyRelatedField(
        source="recipe", queryset=Recipe.objects.all(), write_only=True
    )

    class Meta:
        model = SavedRecipe
        fields = ["id", "recipe", "recipe_id", "created_at"]
        read_only_fields = ["id", "created_at"]
