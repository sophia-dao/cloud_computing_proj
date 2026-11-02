"""
GET /api/recipes/ search and filtering (issue #13).
Contract: docs/api-design.md section 19.1.
"""

from unittest import skipUnless

from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework import status
from rest_framework.test import APITestCase

from apps.recipes.filters import ALLERGEN_FILTERING_UNAVAILABLE, allergen_filtering_available
from apps.recipes.models import Tag
from apps.users.models import (
    Allergen,
    Tag as UserTag,
    User,
    UserAllergy,
    UserPreference,
)

from .factories import make_ingredient, make_recipe, make_tag, make_user

LIST_URL = "/api/recipes/"
T = Tag.TagType


class RecipeSearchAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.korean = make_tag("Korean", T.CUISINE)
        cls.vietnamese = make_tag("Vietnamese", T.CUISINE)
        cls.italian = make_tag("Italian", T.CUISINE)
        cls.vegan = make_tag("Vegan", T.DIET)
        cls.vegetarian = make_tag("Vegetarian", T.DIET)
        cls.halal = make_tag("Halal", T.DIET)
        cls.cheap = make_tag("Cheap", T.COST)
        cls.quick = make_tag("Quick", T.OTHER)

        rice = make_ingredient("Rice")
        chicken = make_ingredient("Chicken")
        tofu = make_ingredient("Tofu")

        def recipe(name, tags, ingredients=(rice,)):
            return make_recipe(name, ingredients=ingredients, tags=tags)

        cls.kimchi_rice = recipe("Kimchi Fried Rice", [cls.korean, cls.vegetarian, cls.cheap, cls.quick])
        cls.chicken_rice = recipe("Chicken Fried Rice", [cls.korean, cls.halal], (rice, chicken))
        cls.tofu_pho = recipe("Tofu Pho", [cls.vietnamese, cls.vegan, cls.vegetarian], (tofu,))
        cls.banh_mi = recipe("Chicken Banh Mi", [cls.vietnamese, cls.halal, cls.cheap], (chicken,))
        cls.risotto = recipe("Mushroom Risotto", [cls.italian, cls.vegetarian])

    def names(self, query=None, expected_status=status.HTTP_200_OK):
        response = self.client.get(LIST_URL, query or {})
        self.assertEqual(response.status_code, expected_status, response.data)
        return [r["name"] for r in response.data["results"]]

    # --- Browsing and search -------------------------------------------------

    def test_guest_can_browse_without_authentication(self):
        self.assertEqual(len(self.names()), 5)

    def test_search_is_case_insensitive_on_name(self):
        self.assertEqual(
            self.names({"search": "FRIED rice"}),
            ["Chicken Fried Rice", "Kimchi Fried Rice"],
        )

    def test_search_ignores_surrounding_whitespace(self):
        self.assertEqual(self.names({"search": "  pho "}), ["Tofu Pho"])

    def test_search_with_no_match_returns_empty_page(self):
        self.assertEqual(self.names({"search": "lasagna"}), [])

    # --- Tag filters ---------------------------------------------------------

    def test_cuisine_filter(self):
        self.assertEqual(
            self.names({"cuisine": "korean"}),
            ["Chicken Fried Rice", "Kimchi Fried Rice"],
        )

    def test_multiple_cuisines_match_any(self):
        self.assertEqual(
            self.names({"cuisine": ["korean", "italian"]}),
            ["Chicken Fried Rice", "Kimchi Fried Rice", "Mushroom Risotto"],
        )

    def test_diet_filter(self):
        self.assertEqual(self.names({"diet": "vegan"}), ["Tofu Pho"])

    def test_multiple_diets_match_all(self):
        self.assertEqual(
            self.names({"diet": ["vegan", "vegetarian"]}), ["Tofu Pho"]
        )

    def test_cost_and_other_filters(self):
        self.assertEqual(
            self.names({"cost": "cheap"}),
            ["Chicken Banh Mi", "Kimchi Fried Rice"],
        )
        self.assertEqual(self.names({"other": "quick"}), ["Kimchi Fried Rice"])

    def test_tag_id_filter(self):
        self.assertEqual(
            self.names({"tag": self.halal.id}),
            ["Chicken Banh Mi", "Chicken Fried Rice"],
        )

    def test_combined_search_and_filters(self):
        self.assertEqual(
            self.names({"search": "rice", "cuisine": "korean", "diet": "vegetarian"}),
            ["Kimchi Fried Rice"],
        )

    def test_filters_across_types_are_combined_with_and(self):
        self.assertEqual(
            self.names({"cuisine": "vietnamese", "cost": "cheap"}),
            ["Chicken Banh Mi"],
        )

    def test_recipe_matching_several_selected_tags_appears_once(self):
        # Kimchi Fried Rice has Korean and Vegetarian; Tofu Pho has
        # Vegetarian and Vegan. ANY-matching on tag IDs across one type
        # must not duplicate either.
        names = self.names(
            {"cuisine": ["korean", "vietnamese"], "diet": "vegetarian"}
        )
        self.assertEqual(names, ["Kimchi Fried Rice", "Tofu Pho"])
        self.assertEqual(len(names), len(set(names)))

    # --- Validation ----------------------------------------------------------

    def test_unknown_cuisine_returns_400(self):
        response = self.client.get(LIST_URL, {"cuisine": "martian"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cuisine", response.data)

    def test_invalid_tag_id_returns_400(self):
        response = self.client.get(LIST_URL, {"tag": "abc"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("tag", response.data)

    def test_tag_name_of_wrong_type_returns_400(self):
        response = self.client.get(LIST_URL, {"diet": "korean"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @skipUnless(not allergen_filtering_available(), "Allergen filtering is now available")
    def test_allergy_filter_is_rejected_until_ingredients_have_allergens(self):
        Allergen.objects.create(name="Peanut")
        response = self.client.get(LIST_URL, {"allergy": "peanut"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            [str(m) for m in response.data["allergy"]],
            [ALLERGEN_FILTERING_UNAVAILABLE],
        )

    # --- Pagination ----------------------------------------------------------

    def test_page_size_parameter(self):
        response = self.client.get(LIST_URL, {"page_size": 2})
        self.assertEqual(response.data["count"], 5)
        self.assertEqual(len(response.data["results"]), 2)

    def test_filtered_count_reflects_filters(self):
        response = self.client.get(LIST_URL, {"diet": "vegetarian", "page_size": 1})
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(len(response.data["results"]), 1)

    # --- Efficiency ----------------------------------------------------------

    def count_queries(self, query):
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(LIST_URL, query)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return len(ctx)

    def test_filtered_query_count_does_not_grow_with_recipes(self):
        query = {"search": "e", "cuisine": ["korean", "vietnamese"], "diet": "halal"}
        few = self.count_queries(query)
        for i in range(10):
            make_recipe(f"Extra Halal Chicken {i}", tags=[self.korean, self.halal, self.quick])
        many = self.count_queries(query)
        self.assertEqual(few, many)


class RecipeSearchUserDefaultsAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.korean = make_tag("Korean", T.CUISINE)
        cls.vietnamese = make_tag("Vietnamese", T.CUISINE)
        cls.halal = make_tag("Halal", T.DIET)

        cls.bibimbap = make_recipe("Bibimbap", tags=[cls.korean])
        cls.bulgogi = make_recipe("Halal Bulgogi", tags=[cls.korean, cls.halal])
        cls.pho = make_recipe("Halal Pho", tags=[cls.vietnamese, cls.halal])
        cls.spring_rolls = make_recipe("Spring Rolls", tags=[cls.vietnamese])

        cls.auth_user = make_user()
        app_user = User.objects.create(auth_user=cls.auth_user)
        UserPreference.objects.create(
            user=app_user,
            tag=UserTag.objects.create(name="Vietnamese", type=UserTag.TagType.CUISINE),
        )
        UserPreference.objects.create(
            user=app_user,
            tag=UserTag.objects.create(name="Halal", type=UserTag.TagType.DIET),
        )
        UserAllergy.objects.create(
            user=app_user, allergen=Allergen.objects.create(name="Peanut")
        )

        # Another user with different preferences, never applied to auth_user.
        other_auth = make_user()
        other = User.objects.create(auth_user=other_auth)
        UserPreference.objects.create(
            user=other,
            tag=UserTag.objects.create(name="Korean", type=UserTag.TagType.CUISINE),
        )

    def names(self, query=None):
        response = self.client.get(LIST_URL, query or {})
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        return [r["name"] for r in response.data["results"]]

    def test_guest_gets_no_defaults(self):
        self.assertEqual(len(self.names()), 4)

    def test_signed_in_user_gets_saved_preferences(self):
        self.client.force_authenticate(self.auth_user)
        self.assertEqual(self.names(), ["Halal Pho"])

    def test_explicit_cuisine_replaces_saved_cuisine_but_keeps_saved_diet(self):
        self.client.force_authenticate(self.auth_user)
        self.assertEqual(self.names({"cuisine": "korean"}), ["Halal Bulgogi"])

    def test_use_preferences_false_shows_everything(self):
        self.client.force_authenticate(self.auth_user)
        self.assertEqual(len(self.names({"use_preferences": "false"})), 4)

    def test_query_parameter_cannot_load_another_users_defaults(self):
        self.assertEqual(len(self.names({"user": 1, "user_id": 1})), 4)


@skipUnless(allergen_filtering_available(), "Ingredients are not linked to Allergens yet")
class RecipeAllergenExclusionAPITests(APITestCase):
    """Runs automatically once Ingredient gains its `allergens` relationship."""

    @classmethod
    def setUpTestData(cls):
        cls.peanut = Allergen.objects.create(name="Peanut")
        peanut_butter = make_ingredient("Peanut Butter")
        peanut_butter.allergens.add(cls.peanut)
        noodles = make_ingredient("Noodles")

        make_recipe("Peanut Noodles", ingredients=[noodles, peanut_butter])
        make_recipe("Plain Noodles", ingredients=[noodles])

    def test_recipe_with_excluded_allergen_is_not_returned(self):
        response = self.client.get(LIST_URL, {"allergy": "peanut"})
        self.assertEqual(
            [r["name"] for r in response.data["results"]], ["Plain Noodles"]
        )
