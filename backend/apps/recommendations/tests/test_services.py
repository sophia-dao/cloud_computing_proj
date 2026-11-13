from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from apps.recipes.models import Tag
from apps.recommendations.services import (
    AVAILABLE_ONLY,
    PARTIAL_MATCH,
    RecommendationService,
    saved_settings,
)

from .factories import (
    ids,
    make_allergen,
    make_app_user,
    make_ingredient,
    make_ingredients,
    make_recipe,
    make_tag,
    save_allergies,
    save_preferences,
)


def names(ingredients):
    return [ingredient.name for ingredient in ingredients]


class ServiceTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.A, cls.B, cls.C, cls.D, cls.E, cls.F = make_ingredients("A", "B", "C", "D", "E", "F")

    def setUp(self):
        self.service = RecommendationService()

    def recipe_names(self, have, mode, **options):
        return [r.recipe.name for r in self.service.recommend(ids(*have), mode, **options)]

    def result_for(self, recipe_name, have, mode):
        for result in self.service.recommend(ids(*have), mode):
            if result.recipe.name == recipe_name:
                return result
        self.fail(f"{recipe_name} not in results")


class AvailableOnlyTests(ServiceTestCase):
    def test_required_subset_of_user_ingredients(self):
        make_recipe("Only A", required=[self.A])
        make_recipe("A and B", required=[self.A, self.B])
        make_recipe("A and D", required=[self.A, self.D])
        have = [self.A, self.B, self.C]
        self.assertEqual(self.recipe_names(have, AVAILABLE_ONLY), ["Only A", "A and B"])

    def test_recipe_need_not_use_every_user_ingredient(self):
        make_recipe("A and C", required=[self.A, self.C])
        have = [self.A, self.B, self.C, self.D, self.E]
        self.assertEqual(self.recipe_names(have, AVAILABLE_ONLY), ["A and C"])

    def test_missing_optional_ingredient_still_matches(self):
        make_recipe("Omelette", required=[self.A, self.B], optional=[self.C])
        result = self.result_for("Omelette", [self.A, self.B], AVAILABLE_ONLY)
        self.assertEqual(result.match_score, 1.0)
        self.assertEqual(names(result.available_ingredients), ["A", "B"])
        self.assertEqual(result.missing_ingredients, [])
        self.assertEqual(names(result.optional_missing_ingredients), ["C"])


class PartialMatchTests(ServiceTestCase):
    def test_matched_missing_and_score(self):
        make_recipe("ABDE", required=[self.A, self.B, self.D, self.E])
        result = self.result_for("ABDE", [self.A, self.B, self.C], PARTIAL_MATCH)
        self.assertEqual(names(result.available_ingredients), ["A", "B"])
        self.assertEqual(names(result.missing_ingredients), ["D", "E"])
        self.assertEqual(result.match_score, 0.5)

    def test_optional_ingredients_do_not_change_score(self):
        make_recipe("Req ABC opt DE", required=[self.A, self.B, self.C], optional=[self.D, self.E])
        result = self.result_for("Req ABC opt DE", [self.A, self.B, self.D], PARTIAL_MATCH)
        self.assertAlmostEqual(result.match_score, 2 / 3)
        self.assertEqual(names(result.available_ingredients), ["A", "B"])
        self.assertEqual(names(result.missing_ingredients), ["C"])
        self.assertEqual(names(result.optional_missing_ingredients), ["E"])

    def test_stronger_matches_rank_first(self):
        make_recipe("Recipe 2", required=[self.A, self.D, self.E, self.F])
        make_recipe("Recipe 1", required=[self.A, self.B, self.C, self.D])
        results = self.service.recommend(ids(self.A, self.B, self.C), PARTIAL_MATCH)
        self.assertEqual([r.recipe.name for r in results], ["Recipe 1", "Recipe 2"])
        self.assertEqual([r.match_score for r in results], [0.75, 0.25])

    def test_full_matches_included_and_ranked_first(self):
        make_recipe("Half", required=[self.A, self.D])
        make_recipe("Full", required=[self.A])
        self.assertEqual(self.recipe_names([self.A, self.B], PARTIAL_MATCH), ["Full", "Half"])

    def test_no_overlap_is_not_a_match(self):
        make_recipe("CD", required=[self.C, self.D])
        have = [self.A, self.B]
        self.assertEqual(self.recipe_names(have, PARTIAL_MATCH), [])
        self.assertEqual(self.recipe_names(have, AVAILABLE_ONLY), [])

    def test_matching_only_an_optional_ingredient_is_not_a_match(self):
        make_recipe("Needs C, optional A", required=[self.C], optional=[self.A])
        self.assertEqual(self.recipe_names([self.A], PARTIAL_MATCH), [])

    def test_equal_scores_break_ties_by_recipe_id(self):
        first = make_recipe("Zucchini thing", required=[self.A, self.D])
        second = make_recipe("Apple thing", required=[self.A, self.E])
        results = self.service.recommend(ids(self.A), PARTIAL_MATCH)
        self.assertEqual([r.recipe.id for r in results], [first.id, second.id])


class InputHandlingTests(ServiceTestCase):
    def test_duplicate_ids_do_not_inflate_scores(self):
        make_recipe("ABDE", required=[self.A, self.B, self.D, self.E])
        dupes = self.service.recommend(ids(self.A, self.A, self.B, self.B, self.C), PARTIAL_MATCH)
        self.assertEqual(dupes[0].match_score, 0.5)
        self.assertEqual(names(dupes[0].available_ingredients), ["A", "B"])

    def test_empty_input_returns_no_results(self):
        make_recipe("A", required=[self.A])
        for mode in (AVAILABLE_ONLY, PARTIAL_MATCH):
            self.assertEqual(self.service.recommend([], mode), [])

    def test_recipes_without_required_ingredients_are_skipped_safely(self):
        make_recipe("Only optional", optional=[self.A])
        make_recipe("No ingredients")
        make_recipe("Normal", required=[self.A])
        for mode in (AVAILABLE_ONLY, PARTIAL_MATCH):
            self.assertEqual(self.recipe_names([self.A, self.B], mode), ["Normal"])

    def test_invalid_mode_rejected(self):
        with self.assertRaises(ValueError):
            self.service.recommend(ids(self.A), "MAGIC_AI_MODE")

    def test_same_request_gives_same_order(self):
        for i in range(6):
            make_recipe(f"Recipe {i}", required=[self.A, [self.B, self.C, self.D][i % 3]])
        orders = [
            [r.recipe.id for r in self.service.recommend(ids(self.A, self.B), PARTIAL_MATCH)]
            for _ in range(3)
        ]
        self.assertEqual(orders[0], orders[1])
        self.assertEqual(orders[1], orders[2])


class TagFilterTests(ServiceTestCase):
    """Same rules as recipe search (recipes.filters): CUISINE/COST any, DIET/OTHER all."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.vietnamese = make_tag("Vietnamese", Tag.TagType.CUISINE)
        cls.korean = make_tag("Korean", Tag.TagType.CUISINE)
        cls.vegan = make_tag("Vegan", Tag.TagType.DIET)
        cls.halal = make_tag("Halal", Tag.TagType.DIET)
        cls.cheap = make_tag("Cheap", Tag.TagType.COST)

    def test_single_tag(self):
        make_recipe("Pho", required=[self.A], tags=[self.vietnamese])
        make_recipe("Bibimbap", required=[self.A], tags=[self.korean])
        self.assertEqual(self.recipe_names([self.A], PARTIAL_MATCH, tag_ids=[self.vietnamese.id]), ["Pho"])

    def test_cuisine_tags_match_any(self):
        make_recipe("Pho", required=[self.A], tags=[self.vietnamese])
        make_recipe("Bibimbap", required=[self.A], tags=[self.korean])
        make_recipe("Untagged", required=[self.A])
        found = self.recipe_names([self.A], PARTIAL_MATCH, tag_ids=[self.vietnamese.id, self.korean.id])
        self.assertEqual(found, ["Pho", "Bibimbap"])

    def test_diet_tags_require_all(self):
        make_recipe("Vegan only", required=[self.A], tags=[self.vegan])
        make_recipe("Vegan and halal", required=[self.A], tags=[self.vegan, self.halal])
        found = self.recipe_names([self.A], PARTIAL_MATCH, tag_ids=[self.vegan.id, self.halal.id])
        self.assertEqual(found, ["Vegan and halal"])

    def test_tags_do_not_change_scores(self):
        make_recipe("Tagged ABCD", required=[self.A, self.B, self.C, self.D], tags=[self.vietnamese, self.cheap])
        results = self.service.recommend(ids(self.A, self.B, self.C), PARTIAL_MATCH, tag_ids=[self.cheap.id])
        self.assertEqual(results[0].match_score, 0.75)

    def test_unknown_tag_rejected(self):
        with self.assertRaises(ValueError):
            self.service.recommend(ids(self.A), PARTIAL_MATCH, tag_ids=[999999])


class AllergenTests(ServiceTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.peanut = make_allergen("Peanut")
        cls.milk = make_allergen("Milk")
        cls.peanut_butter = make_ingredient("Peanut Butter", allergens=[cls.peanut])
        cls.cheese = make_ingredient("Cheese", allergens=[cls.milk])
        cls.mystery = make_ingredient("Mystery Sauce", verified=False)

    def test_known_conflict_excluded(self):
        make_recipe("Satay", required=[self.A, self.peanut_butter])
        make_recipe("Plain", required=[self.A])
        found = self.recipe_names([self.A], PARTIAL_MATCH, allergen_ids=[self.peanut.id])
        self.assertEqual(found, ["Plain"])

    def test_conflict_in_optional_ingredient_excluded(self):
        make_recipe("Noodles with optional peanut", required=[self.A], optional=[self.peanut_butter])
        self.assertEqual(self.recipe_names([self.A], AVAILABLE_ONLY, allergen_ids=[self.peanut.id]), [])

    def test_unverified_ingredient_not_treated_as_safe(self):
        make_recipe("Mystery dish", required=[self.A, self.mystery])
        self.assertEqual(self.recipe_names([self.A], PARTIAL_MATCH, allergen_ids=[self.peanut.id]), [])

    def test_other_allergens_do_not_exclude(self):
        make_recipe("Cheese toast", required=[self.A, self.cheese])
        found = self.recipe_names([self.A], PARTIAL_MATCH, allergen_ids=[self.peanut.id])
        self.assertEqual(found, ["Cheese toast"])

    def test_without_allergen_filter_nothing_is_excluded(self):
        make_recipe("Satay", required=[self.A, self.peanut_butter])
        make_recipe("Mystery dish", required=[self.A, self.mystery])
        self.assertEqual(sorted(self.recipe_names([self.A], PARTIAL_MATCH)), ["Mystery dish", "Satay"])


class PreferenceRankingTests(ServiceTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.vietnamese = make_tag("Vietnamese", Tag.TagType.CUISINE)
        cls.italian = make_tag("Italian", Tag.TagType.CUISINE)
        cls.vegan = make_tag("Vegan", Tag.TagType.DIET)

    def test_preferred_recipe_ranks_above_better_ingredient_match(self):
        make_recipe("Pasta", required=[self.A], tags=[self.italian])
        make_recipe("Pho", required=[self.A, self.D], tags=[self.vietnamese])
        self.assertEqual(self.recipe_names([self.A], PARTIAL_MATCH), ["Pasta", "Pho"])
        preferred = self.recipe_names([self.A], PARTIAL_MATCH, preferred_tag_ids=[self.vietnamese.id])
        self.assertEqual(preferred, ["Pho", "Pasta"])

    def test_more_matching_preferences_rank_higher(self):
        make_recipe("Neither", required=[self.A])
        make_recipe("Vietnamese only", required=[self.A], tags=[self.vietnamese])
        make_recipe("Vegan pho", required=[self.A], tags=[self.vietnamese, self.vegan])
        found = self.recipe_names(
            [self.A], AVAILABLE_ONLY, preferred_tag_ids=[self.vietnamese.id, self.vegan.id]
        )
        self.assertEqual(found, ["Vegan pho", "Vietnamese only", "Neither"])

    def test_preferences_never_hide_recipes_or_change_scores(self):
        make_recipe("Pasta", required=[self.A, self.B], tags=[self.italian])
        results = self.service.recommend(ids(self.A), PARTIAL_MATCH, preferred_tag_ids=[self.vietnamese.id])
        self.assertEqual([r.recipe.name for r in results], ["Pasta"])
        self.assertEqual(results[0].match_score, 0.5)

    def test_within_preference_group_ingredient_match_decides(self):
        make_recipe("Pho half", required=[self.A, self.D], tags=[self.vietnamese])
        make_recipe("Pho full", required=[self.A], tags=[self.vietnamese])
        found = self.recipe_names([self.A], PARTIAL_MATCH, preferred_tag_ids=[self.vietnamese.id])
        self.assertEqual(found, ["Pho full", "Pho half"])


class SavedSettingsTests(ServiceTestCase):
    def test_reads_only_this_users_allergies_and_diet_cuisine_preferences(self):
        vegan = make_tag("Vegan", Tag.TagType.DIET)
        korean = make_tag("Korean", Tag.TagType.CUISINE)
        cheap = make_tag("Cheap", Tag.TagType.COST)
        quick = make_tag("Quick", Tag.TagType.OTHER)
        peanut, milk = make_allergen("Peanut"), make_allergen("Milk")
        _, me = make_app_user()
        _, someone_else = make_app_user()
        save_preferences(me, vegan, korean, cheap, quick)
        save_allergies(me, peanut)
        save_preferences(someone_else, make_tag("Italian", Tag.TagType.CUISINE))
        save_allergies(someone_else, milk)

        settings = saved_settings(me)
        self.assertEqual(settings.preference_tag_ids, {vegan.id, korean.id})
        self.assertEqual(settings.allergen_ids, {peanut.id})

    def test_guest_has_no_saved_settings(self):
        settings = saved_settings(None)
        self.assertEqual(settings.preference_tag_ids, frozenset())
        self.assertEqual(settings.allergen_ids, frozenset())


class ServiceQueryEfficiencyTests(ServiceTestCase):
    """Query count must not grow with the number of recipes or ingredients."""

    def count_queries(self, mode, **options):
        with CaptureQueriesContext(connection) as ctx:
            self.service.recommend(ids(self.A, self.B, self.C), mode, **options)
        return len(ctx)

    def test_query_count_constant(self):
        tag = make_tag("Quick", Tag.TagType.OTHER)
        cuisine = make_tag("Korean", Tag.TagType.CUISINE)
        peanut = make_allergen("Peanut")
        options = {"tag_ids": [tag.id], "allergen_ids": [peanut.id], "preferred_tag_ids": [cuisine.id]}
        # Matches in both modes, so the small case also loads ingredient details.
        make_recipe("First", required=[self.A], optional=[self.E], tags=[tag, cuisine])
        small = {mode: self.count_queries(mode, **options) for mode in (AVAILABLE_ONLY, PARTIAL_MATCH)}
        for i in range(15):
            make_recipe(
                f"More {i}",
                required=[self.A, self.B, [self.C, self.D, self.E][i % 3]],
                optional=[self.F],
                tags=[tag] + ([cuisine] if i % 2 else []),
            )
        for mode in (AVAILABLE_ONLY, PARTIAL_MATCH):
            self.assertEqual(small[mode], self.count_queries(mode, **options), mode)
