from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import QueryDict
from django.test import RequestFactory, TestCase
from unittest.mock import patch

from rest_framework import serializers

from apps.recipes.filters import (
    MAX_SEARCH_LENGTH,
    MAX_VALUES_PER_FILTER,
    ALLERGEN_FILTERING_UNAVAILABLE,
    MatchMode,
    RecipeFilterCriteria,
    apply_user_defaults,
    get_request_application_user,
    parse_recipe_filters,
)
from apps.recipes.models import Tag
from apps.users.models import (
    Allergen,
    Tag as UserTag,
    User,
    UserAllergy,
    UserPreference,
)

# Ingredients are not yet linked to Allergens, so allergen resolution is
# exercised with filtering forced on; the unavailable path is tested separately.
allergen_filtering_on = patch(
    "apps.recipes.filters.allergen_filtering_available", return_value=True
)


def params(query_string):
    return QueryDict(query_string)


class RecipeFilterTestData(TestCase):
    @classmethod
    def setUpTestData(cls):
        T = Tag.TagType
        cls.korean = Tag.objects.create(name="Korean", type=T.CUISINE)
        cls.vietnamese = Tag.objects.create(name="Vietnamese", type=T.CUISINE)
        cls.vegan = Tag.objects.create(name="Vegan", type=T.DIET)
        cls.halal = Tag.objects.create(name="Halal", type=T.DIET)
        cls.cheap = Tag.objects.create(name="Cheap", type=T.COST)
        cls.quick = Tag.objects.create(name="Quick", type=T.OTHER)
        # Same name as a cuisine-type value but a different type.
        cls.korean_other = Tag.objects.create(name="Korean", type=T.OTHER)

        cls.peanut = Allergen.objects.create(name="Peanut")
        cls.shellfish = Allergen.objects.create(name="Shellfish")
        cls.milk = Allergen.objects.create(name="Milk")


class ParseRecipeFiltersTests(RecipeFilterTestData):
    def assert_invalid(self, query_string, field):
        with self.assertRaises(serializers.ValidationError) as ctx:
            parse_recipe_filters(params(query_string))
        self.assertIn(field, ctx.exception.detail)
        return ctx.exception.detail[field]

    def test_no_parameters_returns_empty_criteria_without_queries(self):
        with self.assertNumQueries(0):
            criteria = parse_recipe_filters(params(""))

        self.assertTrue(criteria.is_empty)
        self.assertTrue(criteria.use_preferences)

    def test_search_is_stripped(self):
        criteria = parse_recipe_filters(params("search=%20%20fried%20rice%20"))
        self.assertEqual(criteria.search, "fried rice")

    def test_search_too_long_is_rejected(self):
        self.assert_invalid(f"search={'a' * (MAX_SEARCH_LENGTH + 1)}", "search")

    def test_pagination_and_unknown_parameters_are_ignored(self):
        criteria = parse_recipe_filters(params("page=2&page_size=10&foo=bar"))
        self.assertTrue(criteria.is_empty)

    def test_cuisine_name_is_case_insensitive(self):
        criteria = parse_recipe_filters(params("cuisine=kOrEaN"))

        self.assertEqual(
            criteria.tag_ids_by_type,
            {Tag.TagType.CUISINE: frozenset({self.korean.id})},
        )

    def test_name_filter_only_matches_its_own_tag_type(self):
        criteria = parse_recipe_filters(params("cuisine=korean"))

        self.assertNotIn(Tag.TagType.OTHER, criteria.tag_ids_by_type)
        self.assertNotIn(
            self.korean_other.id,
            criteria.tag_ids_by_type[Tag.TagType.CUISINE],
        )

    def test_repeated_cuisine_values_are_any_match(self):
        criteria = parse_recipe_filters(
            params("cuisine=korean&cuisine=vietnamese")
        )

        self.assertEqual(
            criteria.tag_ids_by_type[Tag.TagType.CUISINE],
            {self.korean.id, self.vietnamese.id},
        )
        self.assertEqual(
            criteria.match_mode(Tag.TagType.CUISINE), MatchMode.ANY
        )

    def test_repeated_diet_values_are_all_match(self):
        criteria = parse_recipe_filters(params("diet=vegan&diet=halal"))

        self.assertEqual(
            criteria.tag_ids_by_type[Tag.TagType.DIET],
            {self.vegan.id, self.halal.id},
        )
        self.assertEqual(criteria.match_mode(Tag.TagType.DIET), MatchMode.ALL)

    def test_tag_ids_are_grouped_by_their_type(self):
        criteria = parse_recipe_filters(
            params(f"tag={self.korean.id}&tag={self.cheap.id}&tag={self.quick.id}")
        )

        self.assertEqual(
            criteria.tag_ids_by_type,
            {
                Tag.TagType.CUISINE: frozenset({self.korean.id}),
                Tag.TagType.COST: frozenset({self.cheap.id}),
                Tag.TagType.OTHER: frozenset({self.quick.id}),
            },
        )

    def test_same_tag_by_id_and_name_is_deduplicated(self):
        criteria = parse_recipe_filters(
            params(f"tag={self.vegan.id}&diet=Vegan")
        )
        self.assertEqual(
            criteria.tag_ids_by_type[Tag.TagType.DIET], {self.vegan.id}
        )

    @allergen_filtering_on
    def test_combined_filters(self, _available):
        criteria = parse_recipe_filters(
            params("search=rice&cuisine=korean&diet=vegan&allergy=peanut")
        )

        self.assertEqual(criteria.search, "rice")
        self.assertEqual(
            criteria.tag_ids_by_type,
            {
                Tag.TagType.CUISINE: frozenset({self.korean.id}),
                Tag.TagType.DIET: frozenset({self.vegan.id}),
            },
        )
        self.assertEqual(criteria.excluded_allergen_ids, {self.peanut.id})

    @allergen_filtering_on
    def test_allergy_names_and_allergen_ids_are_combined(self, _available):
        criteria = parse_recipe_filters(
            params(f"allergy=PEANUT&allergen={self.shellfish.id}")
        )
        self.assertEqual(
            criteria.excluded_allergen_ids,
            {self.peanut.id, self.shellfish.id},
        )

    @allergen_filtering_on
    def test_lookups_use_one_tag_and_one_allergen_query(self, _available):
        with self.assertNumQueries(2):
            parse_recipe_filters(
                params(
                    "cuisine=korean&cuisine=vietnamese&diet=vegan&cost=cheap"
                    f"&other=quick&tag={self.halal.id}"
                    f"&allergy=peanut&allergy=milk&allergen={self.shellfish.id}"
                )
            )

    def test_unknown_cuisine_is_rejected(self):
        messages = self.assert_invalid("cuisine=korean&cuisine=martian", "cuisine")
        self.assertEqual(len(messages), 1)
        self.assertIn("martian", str(messages[0]))

    @allergen_filtering_on
    def test_unknown_allergy_is_rejected_not_ignored(self, _available):
        self.assert_invalid("allergy=peanutt", "allergy")

    @patch("apps.recipes.filters.allergen_filtering_available", return_value=False)
    def test_allergy_filters_rejected_while_ingredients_lack_allergens(self, _available):
        for query, field in (("allergy=peanut", "allergy"), (f"allergen={self.peanut.id}", "allergen")):
            messages = self.assert_invalid(query, field)
            self.assertEqual([str(m) for m in messages], [ALLERGEN_FILTERING_UNAVAILABLE])

    def test_non_numeric_tag_id_is_rejected(self):
        self.assert_invalid("tag=abc", "tag")

    def test_zero_or_negative_ids_are_rejected(self):
        self.assert_invalid("tag=0", "tag")
        self.assert_invalid("allergen=-1", "allergen")

    def test_nonexistent_tag_id_is_rejected(self):
        self.assert_invalid("tag=99999", "tag")

    @allergen_filtering_on
    def test_nonexistent_allergen_id_is_rejected(self, _available):
        self.assert_invalid("allergen=99999", "allergen")

    def test_blank_value_is_rejected(self):
        self.assert_invalid("diet=%20", "diet")

    def test_too_many_values_are_rejected(self):
        query = "&".join(["cuisine=korean"] * (MAX_VALUES_PER_FILTER + 1))
        self.assert_invalid(query, "cuisine")

    def test_sql_like_input_is_treated_as_a_plain_value(self):
        self.assert_invalid("cuisine=korean'%20OR%201=1--", "cuisine")
        self.assertEqual(Tag.objects.count(), 7)

    def test_use_preferences_flag(self):
        self.assertFalse(
            parse_recipe_filters(params("use_preferences=false")).use_preferences
        )
        self.assertTrue(
            parse_recipe_filters(params("use_preferences=TRUE")).use_preferences
        )
        self.assert_invalid("use_preferences=maybe", "use_preferences")

    def test_errors_for_several_fields_are_reported_together(self):
        with self.assertRaises(serializers.ValidationError) as ctx:
            parse_recipe_filters(params("tag=abc&use_preferences=maybe"))
        self.assertEqual(
            set(ctx.exception.detail), {"tag", "use_preferences"}
        )


class UserDefaultsTests(RecipeFilterTestData):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        AuthUser = get_user_model()

        cls.auth_user = AuthUser.objects.create_user(
            username="alice", password="TestPassword123!"
        )
        cls.user = User.objects.create(auth_user=cls.auth_user)

        # Saved preferences point at users.Tag; filters bridge them to the
        # recipes.Tag with the same type and name (see _saved_preference_tags).
        UT = UserTag.TagType
        cls.pref_vietnamese = UserTag.objects.create(name="vietnamese", type=UT.CUISINE)
        cls.pref_halal = UserTag.objects.create(name="Halal", type=UT.DIET)
        cls.pref_cheap = UserTag.objects.create(name="Cheap", type=UT.COST)
        cls.pref_unmatched = UserTag.objects.create(name="Keto", type=UT.DIET)

        UserPreference.objects.create(user=cls.user, tag=cls.pref_vietnamese)
        UserPreference.objects.create(user=cls.user, tag=cls.pref_halal)
        UserAllergy.objects.create(user=cls.user, allergen=cls.peanut)

        other_auth = AuthUser.objects.create_user(
            username="bob", password="TestPassword123!"
        )
        cls.other_user = User.objects.create(auth_user=other_auth)
        UserPreference.objects.create(user=cls.other_user, tag=cls.pref_cheap)
        UserAllergy.objects.create(user=cls.other_user, allergen=cls.milk)

    def defaults_for(self, query_string, user):
        return apply_user_defaults(parse_recipe_filters(params(query_string)), user)

    def test_guest_criteria_are_unchanged(self):
        criteria = parse_recipe_filters(params("cuisine=korean"))

        with self.assertNumQueries(0):
            self.assertIs(apply_user_defaults(criteria, None), criteria)

    def test_saved_preferences_and_allergies_apply_by_default(self):
        criteria = self.defaults_for("", self.user)

        self.assertEqual(
            criteria.tag_ids_by_type,
            {
                Tag.TagType.CUISINE: frozenset({self.vietnamese.id}),
                Tag.TagType.DIET: frozenset({self.halal.id}),
            },
        )
        self.assertEqual(criteria.excluded_allergen_ids, {self.peanut.id})

    def test_explicit_type_replaces_saved_preferences_of_that_type_only(self):
        criteria = self.defaults_for("cuisine=korean", self.user)

        self.assertEqual(
            criteria.tag_ids_by_type[Tag.TagType.CUISINE], {self.korean.id}
        )
        self.assertEqual(
            criteria.tag_ids_by_type[Tag.TagType.DIET], {self.halal.id}
        )

    @allergen_filtering_on
    def test_explicit_allergies_extend_saved_allergies(self, _available):
        criteria = self.defaults_for("allergy=shellfish", self.user)
        self.assertEqual(
            criteria.excluded_allergen_ids, {self.peanut.id, self.shellfish.id}
        )

    def test_use_preferences_false_skips_tags_but_keeps_allergies(self):
        criteria = self.defaults_for("use_preferences=false", self.user)

        self.assertEqual(criteria.tag_ids_by_type, {})
        self.assertEqual(criteria.excluded_allergen_ids, {self.peanut.id})

    def test_other_users_data_is_never_used(self):
        criteria = self.defaults_for("", self.user)

        all_tag_ids = set().union(*criteria.tag_ids_by_type.values())
        self.assertNotIn(self.cheap.id, all_tag_ids)
        self.assertNotIn(self.milk.id, criteria.excluded_allergen_ids)

    def test_saved_preference_without_matching_recipe_tag_is_skipped(self):
        UserPreference.objects.create(user=self.user, tag=self.pref_unmatched)

        criteria = self.defaults_for("", self.user)

        self.assertEqual(
            criteria.tag_ids_by_type[Tag.TagType.DIET], {self.halal.id}
        )

    def test_defaults_use_three_queries(self):
        # Saved allergies, saved preferences, and the recipe Tag bridge.
        criteria = parse_recipe_filters(params(""))
        with self.assertNumQueries(3):
            apply_user_defaults(criteria, self.user)

    def test_result_is_a_new_criteria_object(self):
        original = parse_recipe_filters(params(""))
        merged = apply_user_defaults(original, self.user)

        self.assertIsInstance(merged, RecipeFilterCriteria)
        self.assertEqual(original.tag_ids_by_type, {})


class RequestApplicationUserTests(RecipeFilterTestData):
    def setUp(self):
        self.factory = RequestFactory()
        AuthUser = get_user_model()
        self.auth_user = AuthUser.objects.create_user(
            username="carol", password="TestPassword123!"
        )
        self.user = User.objects.create(auth_user=self.auth_user)

    def request_as(self, auth_user, query_string=""):
        request = self.factory.get(f"/api/recipes/?{query_string}")
        request.user = auth_user
        return request

    def test_guest_has_no_application_user(self):
        self.assertIsNone(get_request_application_user(self.request_as(AnonymousUser())))

    def test_authenticated_user_resolves_to_own_profile(self):
        self.assertEqual(
            get_request_application_user(self.request_as(self.auth_user)),
            self.user,
        )

    def test_query_parameters_cannot_select_another_user(self):
        other_auth = get_user_model().objects.create_user(
            username="dave", password="TestPassword123!"
        )
        other = User.objects.create(auth_user=other_auth)

        request = self.request_as(
            AnonymousUser(), f"user={other.id}&user_id={other.id}"
        )
        self.assertIsNone(get_request_application_user(request))

    def test_suspended_user_gets_no_defaults(self):
        self.user.account_status = User.AccountStatus.SUSPENDED
        self.user.save()

        self.assertIsNone(
            get_request_application_user(self.request_as(self.auth_user))
        )

    def test_authenticated_user_without_application_user(self):
        lone = get_user_model().objects.create_user(
            username="erin", password="TestPassword123!"
        )
        self.assertIsNone(get_request_application_user(self.request_as(lone)))
