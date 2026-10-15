"""
Recipe search and filter parameters (issue #13).

Parses and validates GET /api/recipes/ query parameters into structured
criteria made of canonical Tag and Allergen IDs, and merges an authenticated
user's saved preferences and allergies into those criteria.

This module deliberately does not depend on the Recipe model, which is owned
by issue #4. Translating RecipeFilterCriteria into a Recipe queryset is added
once Recipe, RecipeIngredient, and the Ingredient-Allergen relationship exist.

The contract implemented here is documented in docs/api-design.md,
section 19.1 (proposed, pending team review).
"""

from dataclasses import dataclass, field

from django.db.models import Q
from rest_framework import serializers

from apps.users.models import Allergen, Tag, User, UserAllergy, UserPreference


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
        for tag_id, tag_type in UserPreference.objects.filter(
            user=application_user,
        ).values_list("tag_id", "tag__type"):
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
