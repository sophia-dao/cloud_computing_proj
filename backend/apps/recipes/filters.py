"""
Recipe search and filter parameters (issue #13).

Parses and validates GET /api/recipes/ query parameters into structured
criteria made of canonical Tag and Allergen IDs, merges an authenticated
user's saved preferences and allergies into those criteria, and applies the
criteria to a Recipe queryset.

The contract implemented here is documented in docs/api-design.md,
section 19.1 (proposed, pending team review).

Known gaps, pending team decisions:
- Two Tag models exist: recipes.Tag (used by Recipe.tags) and users.Tag (used
  by UserPreference). Filters resolve against recipes.Tag. Saved preferences
  are bridged by (type, name) in _saved_preference_tags(); delete that bridge
  once the models are consolidated.
- Ingredients are not yet linked to Allergens, so allergen exclusion cannot
  run. Explicit allergy filters are rejected with 400 instead of being
  silently ignored. See allergen_filtering_available().
"""

from dataclasses import dataclass, field

from django.db.models import Exists, OuterRef, Q
from rest_framework import serializers

from apps.ingredients.models import Ingredient
from apps.users.models import Allergen, User, UserAllergy, UserPreference

from .models import Recipe, RecipeIngredient, Tag


MAX_SEARCH_LENGTH = 255

# Upper bound on values per filter parameter so a single request cannot
# produce an unbounded number of lookup conditions.
MAX_VALUES_PER_FILTER = 20


class MatchMode:
    # Recipe needs at least one of the selected Tags of this type.
    ANY = "ANY"
    # Recipe needs every selected Tag of this type.
    ALL = "ALL"


# Semantics for multiple values of the same Tag type. Different Tag types,
# search, and allergen exclusions are always combined with AND.
TAG_TYPE_MATCH_MODES = {
    Tag.TagType.CUISINE: MatchMode.ANY,
    Tag.TagType.COST: MatchMode.ANY,
    Tag.TagType.DIET: MatchMode.ALL,
    Tag.TagType.OTHER: MatchMode.ALL,
}

# User-facing convenience parameters that resolve Tag names of one type.
TAG_NAME_PARAMS = {
    "cuisine": Tag.TagType.CUISINE,
    "diet": Tag.TagType.DIET,
    "cost": Tag.TagType.COST,
    "other": Tag.TagType.OTHER,
}

TAG_ID_PARAM = "tag"
ALLERGEN_ID_PARAM = "allergen"
ALLERGEN_NAME_PARAM = "allergy"
USE_PREFERENCES_PARAM = "use_preferences"

# Expected name of the Ingredient <-> Allergen many-to-many field
# (docs/database-design.md section 13). It does not exist yet.
INGREDIENT_ALLERGEN_FIELD = "allergens"

ALLERGEN_FILTERING_UNAVAILABLE = (
    "Allergen filtering is not available yet: ingredients are not linked "
    "to allergens."
)


def allergen_filtering_available():
    return any(
        f.name == INGREDIENT_ALLERGEN_FIELD for f in Ingredient._meta.get_fields()
    )


@dataclass(frozen=True)
class RecipeFilterCriteria:
    search: str = ""
    # Tag type -> selected canonical Tag IDs of that type.
    tag_ids_by_type: dict = field(default_factory=dict)
    excluded_allergen_ids: frozenset = frozenset()
    use_preferences: bool = True

    def match_mode(self, tag_type):
        return TAG_TYPE_MATCH_MODES[tag_type]

    @property
    def is_empty(self):
        return not (
            self.search or self.tag_ids_by_type or self.excluded_allergen_ids
        )


def parse_recipe_filters(query_params):
    """
    Validate recipe search/filter query parameters.

    Returns RecipeFilterCriteria, or raises serializers.ValidationError
    (HTTP 400) with field-specific messages. Unknown parameters such as
    pagination parameters are ignored.

    Name and ID lookups are resolved with at most one Tag query and one
    Allergen query regardless of how many values are supplied.
    """
    errors = {}

    search = _parse_search(query_params, errors)
    use_preferences = _parse_bool(query_params, USE_PREFERENCES_PARAM, True, errors)

    tag_ids = _parse_ids(query_params, TAG_ID_PARAM, errors)
    tag_names = {
        param: _parse_names(query_params, param, errors)
        for param in TAG_NAME_PARAMS
    }
    allergen_ids = _parse_ids(query_params, ALLERGEN_ID_PARAM, errors)
    allergen_names = _parse_names(query_params, ALLERGEN_NAME_PARAM, errors)

    if (allergen_ids or allergen_names) and not allergen_filtering_available():
        # Rejected rather than ignored: returning recipes the client believes
        # were allergen-filtered would be unsafe.
        for param, values in (
            (ALLERGEN_ID_PARAM, allergen_ids),
            (ALLERGEN_NAME_PARAM, allergen_names),
        ):
            if values:
                errors[param] = [ALLERGEN_FILTERING_UNAVAILABLE]

    if errors:
        raise serializers.ValidationError(errors)

    tags = _resolve_tags(tag_ids, tag_names, errors)
    allergens = _resolve_allergens(allergen_ids, allergen_names, errors)

    if errors:
        raise serializers.ValidationError(errors)

    tag_ids_by_type = {}
    for tag_id, tag_type in tags:
        tag_ids_by_type.setdefault(tag_type, set()).add(tag_id)

    return RecipeFilterCriteria(
        search=search,
        tag_ids_by_type={
            tag_type: frozenset(ids) for tag_type, ids in tag_ids_by_type.items()
        },
        excluded_allergen_ids=frozenset(allergens),
        use_preferences=use_preferences,
    )


def get_request_application_user(request):
    """
    Return the active application User for the authenticated requester,
    or None for Guests.

    Defaults are only ever derived from the requester's own identity; no
    query parameter can select another user's profile.
    """
    if not request.user or not request.user.is_authenticated:
        return None

    return User.objects.filter(
        auth_user=request.user,
        account_status=User.AccountStatus.ACTIVE,
    ).first()


def apply_user_defaults(criteria, application_user):
    """
    Merge an authenticated user's saved data into explicit criteria.

    - Saved allergies are always added to the explicit allergen exclusions.
      They are safety filters and cannot be disabled by query parameters.
    - Saved Tag preferences fill in only the Tag types the request did not
      filter explicitly. An explicit filter for a type replaces the saved
      preferences of that type. use_preferences=false skips them entirely.
    - Guests (application_user is None) get the criteria unchanged.
    """
    if application_user is None:
        return criteria

    saved_allergen_ids = UserAllergy.objects.filter(
        user=application_user,
    ).values_list("allergen_id", flat=True)

    tag_ids_by_type = dict(criteria.tag_ids_by_type)

    if criteria.use_preferences:
        saved_preferences = {}
        for tag_id, tag_type in _saved_preference_tags(application_user):
            saved_preferences.setdefault(tag_type, set()).add(tag_id)

        for tag_type, ids in saved_preferences.items():
            if tag_type not in tag_ids_by_type:
                tag_ids_by_type[tag_type] = frozenset(ids)

    return RecipeFilterCriteria(
        search=criteria.search,
        tag_ids_by_type=tag_ids_by_type,
        excluded_allergen_ids=criteria.excluded_allergen_ids
        | frozenset(saved_allergen_ids),
        use_preferences=criteria.use_preferences,
    )


def filter_recipes(queryset, criteria):
    """
    Apply criteria to a Recipe queryset entirely in the database.

    Relationship conditions use EXISTS subqueries rather than joins, so a
    Recipe is returned at most once without needing distinct(), and the
    queryset's ordering and prefetching are preserved.
    """
    if criteria.search:
        queryset = queryset.filter(name__icontains=criteria.search)

    for tag_type, tag_ids in criteria.tag_ids_by_type.items():
        if criteria.match_mode(tag_type) == MatchMode.ANY:
            queryset = queryset.filter(_has_any_tag(tag_ids))
        else:
            for tag_id in tag_ids:
                queryset = queryset.filter(_has_any_tag([tag_id]))

    # Until ingredients are linked to allergens, saved allergies cannot be
    # enforced here (explicit allergy filters are already rejected by
    # parse_recipe_filters). Tracked in docs/api-design.md section 19.1.
    if criteria.excluded_allergen_ids and allergen_filtering_available():
        queryset = queryset.exclude(
            Exists(
                RecipeIngredient.objects.filter(
                    recipe=OuterRef("pk"),
                    **{
                        f"ingredient__{INGREDIENT_ALLERGEN_FIELD}__in":
                            criteria.excluded_allergen_ids
                    },
                )
            )
        )

    return queryset


def _has_any_tag(tag_ids):
    return Exists(
        Recipe.tags.through.objects.filter(
            recipe_id=OuterRef("pk"),
            tag_id__in=tag_ids,
        )
    )


def _saved_preference_tags(application_user):
    """
    Return (recipes.Tag id, type) pairs for the user's saved preferences.

    TEMPORARY BRIDGE: UserPreference points at users.Tag while recipes use
    recipes.Tag, so preferences are matched by (type, case-insensitive name).
    A preference with no matching recipe Tag is skipped. Replace this with
    the preference IDs directly once the two Tag models are consolidated.
    """
    saved = list(
        UserPreference.objects.filter(user=application_user)
        .values_list("tag__type", "tag__name")
    )
    if not saved:
        return []

    lookup = Q()
    for tag_type, name in saved:
        lookup |= Q(type=tag_type, name__iexact=name)

    return list(Tag.objects.filter(lookup).values_list("id", "type"))


def _parse_search(query_params, errors):
    search = query_params.get("search", "")

    if len(search) > MAX_SEARCH_LENGTH:
        errors["search"] = [
            f"Search must be {MAX_SEARCH_LENGTH} characters or fewer."
        ]
        return ""

    return search.strip()


def _parse_bool(query_params, param, default, errors):
    value = query_params.get(param)

    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False

    errors[param] = ["Must be 'true' or 'false'."]
    return default


def _get_values(query_params, param, errors):
    values = query_params.getlist(param)

    if len(values) > MAX_VALUES_PER_FILTER:
        errors[param] = [
            f"At most {MAX_VALUES_PER_FILTER} values are allowed."
        ]
        return []

    return values


def _parse_ids(query_params, param, errors):
    ids = set()

    for raw in _get_values(query_params, param, errors):
        value = raw.strip()
        if not value.isdigit() or int(value) < 1:
            errors.setdefault(param, []).append(
                f"'{raw}' is not a valid ID."
            )
            continue
        ids.add(int(value))

    return ids


def _parse_names(query_params, param, errors):
    names = set()

    for raw in _get_values(query_params, param, errors):
        value = raw.strip()
        if not value:
            errors.setdefault(param, []).append("Values may not be blank.")
            continue
        if len(value) > 100:
            errors.setdefault(param, []).append(
                "Values must be 100 characters or fewer."
            )
            continue
        names.add(value)

    return names


def _resolve_tags(tag_ids, tag_names, errors):
    """Return a set of (tag_id, tag_type) for all requested Tags."""
    lookup = Q()
    if tag_ids:
        lookup |= Q(id__in=tag_ids)
    for param, names in tag_names.items():
        for name in names:
            lookup |= Q(type=TAG_NAME_PARAMS[param], name__iexact=name)

    if not lookup:
        return set()

    found = list(Tag.objects.filter(lookup).values_list("id", "name", "type"))

    missing_ids = tag_ids - {tag_id for tag_id, _, _ in found}
    if missing_ids:
        errors[TAG_ID_PARAM] = [
            f"Unknown tag ID: {tag_id}." for tag_id in sorted(missing_ids)
        ]

    for param, names in tag_names.items():
        tag_type = TAG_NAME_PARAMS[param]
        known = {
            name.casefold() for _, name, found_type in found
            if found_type == tag_type
        }
        unknown = sorted(n for n in names if n.casefold() not in known)
        if unknown:
            errors[param] = [f"Unsupported {param}: '{n}'." for n in unknown]

    requested_names = {
        (TAG_NAME_PARAMS[param], name.casefold())
        for param, names in tag_names.items()
        for name in names
    }
    return {
        (tag_id, tag_type) for tag_id, name, tag_type in found
        if tag_id in tag_ids or (tag_type, name.casefold()) in requested_names
    }


def _resolve_allergens(allergen_ids, allergen_names, errors):
    """Return the set of Allergen IDs for all requested exclusions."""
    lookup = Q()
    if allergen_ids:
        lookup |= Q(id__in=allergen_ids)
    for name in allergen_names:
        lookup |= Q(name__iexact=name)

    if not lookup:
        return set()

    found = list(Allergen.objects.filter(lookup).values_list("id", "name"))

    missing_ids = allergen_ids - {allergen_id for allergen_id, _ in found}
    if missing_ids:
        errors[ALLERGEN_ID_PARAM] = [
            f"Unknown allergen ID: {allergen_id}."
            for allergen_id in sorted(missing_ids)
        ]

    known_names = {name.casefold() for _, name in found}
    unknown = sorted(n for n in allergen_names if n.casefold() not in known_names)
    if unknown:
        errors[ALLERGEN_NAME_PARAM] = [
            f"Unsupported allergy: '{n}'." for n in unknown
        ]

    requested_names = {n.casefold() for n in allergen_names}
    return {
        allergen_id for allergen_id, name in found
        if allergen_id in allergen_ids or name.casefold() in requested_names
    }
