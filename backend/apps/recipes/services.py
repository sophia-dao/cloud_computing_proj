"""
Recipe submission helpers (Issue #67).

Duplicate titles are only warned about, never blocked: two different people
can genuinely have different recipes with the same name. The frontend asks
GET /api/recipes/duplicates/?name=... before submitting and shows any matches.
"""

from .models import Recipe

MAX_DUPLICATE_MATCHES = 5


def normalize_recipe_name(name):
    """Trim and collapse runs of spaces: "  Kimchi   Fried Rice " -> "Kimchi Fried Rice"."""
    return " ".join(str(name).split())


def find_recipes_with_same_name(name, limit=MAX_DUPLICATE_MATCHES):
    """Existing recipes whose name equals `name`, ignoring case and extra spaces.

    New recipe names are stored normalized (see RecipeWriteSerializer), so a
    case-insensitive exact match on the normalized name is enough.
    """
    normalized = normalize_recipe_name(name)
    if not normalized:
        return Recipe.objects.none()
    return Recipe.objects.filter(name__iexact=normalized).order_by("name", "id")[:limit]
