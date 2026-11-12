"""
Recipe recommendation business logic (Issue #6).

Answers: "Given these available ingredients and filters, which recipes match,
which required ingredients are present or missing, and what is the match score?"

Guests and logged-in users share the same service. It only ever sees
canonical ingredient IDs and never knows where they came from.

Matching rules (docs/api-design.md sections 20.5-20.6):
- AVAILABLE_ONLY: every required ingredient is available.
- PARTIAL_MATCH: at least one required ingredient is available.
- match_score = available required / total required. Optional ingredients
  never count toward eligibility or the score.
- Recipes with no required ingredients can't be scored, so they are never
  recommended (no division by zero, no invented formula).

Tag filters, allergen exclusions and the "unverified ingredients aren't shown
as safe" rule reuse recipes.filters.filter_recipes, so recommendations and
recipe search always agree.

Counting and ranking happen in the database, so the number of queries stays
the same however many recipes exist.
"""

from dataclasses import dataclass, field

from django.db.models import (
    Count,
    Exists,
    F,
    FloatField,
    OuterRef,
    Prefetch,
    Q,
    Value,
    prefetch_related_objects,
)
from django.db.models.functions import Cast, NullIf

from apps.inventory.models import InventoryItem
from apps.recipes.filters import RecipeFilterCriteria, filter_recipes
from apps.recipes.models import Recipe, RecipeIngredient, Tag
from apps.users.models import UserAllergy, UserPreference

AVAILABLE_ONLY = "AVAILABLE_ONLY"
PARTIAL_MATCH = "PARTIAL_MATCH"
MATCH_MODES = (AVAILABLE_ONLY, PARTIAL_MATCH)

# Saved preference types used for ranking (Issue #6: "dietary/cuisine preferences").
RANKING_PREFERENCE_TYPES = (Tag.TagType.DIET, Tag.TagType.CUISINE)

# For logged-in users with saved preferences: recipes matching more of those
# preferences come first, then better ingredient matches, then recipe ID.
# To make preferences only break ties between equal match scores instead,
# swap the first two entries.
PERSONALIZED_ORDERING = ("-preference_matches", "-match_score", "id")
DEFAULT_ORDERING = ("-match_score", "id")


@dataclass
class RecommendationResult:
    recipe: Recipe
    match_score: float
    available_ingredients: list = field(default_factory=list)
    missing_ingredients: list = field(default_factory=list)
    optional_missing_ingredients: list = field(default_factory=list)


@dataclass(frozen=True)
class SavedSettings:
    """A logged-in user's saved allergies and ranking preferences."""

    allergen_ids: frozenset = frozenset()
    preference_tag_ids: frozenset = frozenset()


def saved_inventory_ingredient_ids(auth_user):
    """Ingredient IDs from the logged-in user's own saved inventory.

    The caller passes request.user; no client-supplied ID is ever used.
    """
    return set(
        InventoryItem.objects.filter(user=auth_user).values_list("ingredient_id", flat=True)
    )


def saved_settings(application_user):
    """Saved allergies and DIET/CUISINE preferences for an application user.

    application_user comes from recipes.filters.get_request_application_user,
    which is None for guests (and for accounts that aren't active).
    """
    if application_user is None:
        return SavedSettings()
    allergen_ids = UserAllergy.objects.filter(user=application_user).values_list(
        "allergen_id", flat=True
    )
    preference_tag_ids = UserPreference.objects.filter(
        user=application_user, tag__type__in=RANKING_PREFERENCE_TYPES
    ).values_list("tag_id", flat=True)
    return SavedSettings(
        allergen_ids=frozenset(allergen_ids),
        preference_tag_ids=frozenset(preference_tag_ids),
    )


class RecommendationService:
    def recommend(
        self,
        ingredient_ids,
        match_mode,
        tag_ids=(),
        allergen_ids=(),
        preferred_tag_ids=(),
        limit=None,
    ):
        """Convenience method: ranked results, optionally only the first `limit`."""
        recipes = self.matching_recipes(
            ingredient_ids, match_mode, tag_ids, allergen_ids, preferred_tag_ids
        )
        if limit is not None:
            recipes = recipes[:limit]
        return self.build_results(recipes, ingredient_ids)

    def matching_recipes(
        self,
        ingredient_ids,
        match_mode,
        tag_ids=(),
        allergen_ids=(),
        preferred_tag_ids=(),
    ):
        """Eligible recipes, best first. Lazy: paginate or slice before using.

        - tag_ids and allergen_ids are hard filters (same rules as recipe search).
          With any allergen filter, recipes with an unverified ingredient are
          left out too, so nothing unverified is presented as allergen-safe.
        - preferred_tag_ids only change the order (see PERSONALIZED_ORDERING).
        """
        if match_mode not in MATCH_MODES:
            raise ValueError(f"Unknown match mode: {match_mode!r}")
        available = set(ingredient_ids)
        preferred = set(preferred_tag_ids)

        criteria = RecipeFilterCriteria(
            tag_ids_by_type=self._group_tags_by_type(tag_ids),
            excluded_allergen_ids=frozenset(allergen_ids),
        )
        recipes = filter_recipes(Recipe.objects.all(), criteria)
        if not available:
            return recipes.none()

        # Any eligible recipe in either mode has at least one required
        # ingredient the user has. Narrowing to those first (via the
        # ingredient index) keeps the counting below to likely candidates.
        recipes = recipes.filter(
            Exists(
                RecipeIngredient.objects.filter(
                    recipe=OuterRef("pk"), is_optional=False, ingredient_id__in=available
                )
            )
        )

        required = Q(recipe_ingredients__is_optional=False)
        annotations = {
            "required_total": Count("recipe_ingredients", filter=required, distinct=True),
            "required_available": Count(
                "recipe_ingredients",
                filter=required & Q(recipe_ingredients__ingredient_id__in=available),
                distinct=True,
            ),
        }
        if preferred:
            annotations["preference_matches"] = Count(
                "tags", filter=Q(tags__id__in=preferred), distinct=True
            )
        recipes = recipes.annotate(**annotations).annotate(
            # NullIf turns a zero denominator into NULL instead of a division error.
            match_score=Cast("required_available", FloatField())
            / NullIf(Cast("required_total", FloatField()), Value(0.0)),
        )

        if match_mode == AVAILABLE_ONLY:
            recipes = recipes.filter(required_total__gt=0, required_available=F("required_total"))
        else:
            recipes = recipes.filter(required_total__gt=0, required_available__gt=0)

        return recipes.order_by(*(PERSONALIZED_ORDERING if preferred else DEFAULT_ORDERING))

    def build_results(self, recipes, ingredient_ids):
        """Turn ranked recipes (one page) into results, with one extra query in total."""
        available = set(ingredient_ids)
        recipe_list = list(recipes)
        if not recipe_list:
            return []
        prefetch_related_objects(
            recipe_list,
            Prefetch(
                "recipe_ingredients",
                queryset=RecipeIngredient.objects.select_related("ingredient"),
            ),
        )

        results = []
        for recipe in recipe_list:
            result = RecommendationResult(recipe=recipe, match_score=recipe.match_score)
            # Ingredient lists keep the recipe's own ingredient order.
            for item in recipe.recipe_ingredients.all():
                have_it = item.ingredient_id in available
                if item.is_optional:
                    if not have_it:
                        result.optional_missing_ingredients.append(item.ingredient)
                elif have_it:
                    result.available_ingredients.append(item.ingredient)
                else:
                    result.missing_ingredients.append(item.ingredient)
            results.append(result)
        return results

    def _group_tags_by_type(self, tag_ids):
        """{tag type: tag IDs}, the shape recipes.filters expects. One query."""
        tag_ids = set(tag_ids)
        if not tag_ids:
            return {}
        found = dict(Tag.objects.filter(pk__in=tag_ids).values_list("pk", "type"))
        unknown = sorted(tag_ids - set(found))
        if unknown:
            raise ValueError(f"Unknown tag IDs: {unknown}")
        grouped = {}
        for tag_id, tag_type in found.items():
            grouped.setdefault(tag_type, set()).add(tag_id)
        return {tag_type: frozenset(ids) for tag_type, ids in grouped.items()}
