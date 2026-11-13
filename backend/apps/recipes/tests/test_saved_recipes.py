"""
Saved recipes (Issue #14): save, list, remove, no duplicates, and nobody can
see or remove another user's saved recipes.
"""

from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework import status
from rest_framework.test import APITestCase

from apps.recipes.models import Recipe, SavedRecipe, Tag

URL = "/api/saved-recipes/"

# A guest gets 401 or 403 depending on which authentication class the project
# lists first; either way the request is refused.
GUEST_REFUSED = (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


class SavedRecipeTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model().objects
        cls.alice = users.create_user(username="alice")
        cls.bob = users.create_user(username="bob")
        cls.korean = Tag.objects.create(name="Korean", type=Tag.TagType.CUISINE)
        cls.bibimbap = Recipe.objects.create(name="Bibimbap", instructions="Mix.")
        cls.bibimbap.tags.add(cls.korean)
        cls.pancakes = Recipe.objects.create(name="Pancakes", instructions="Flip.")

    def as_user(self, user):
        self.client.force_authenticate(user)
        return self.client

    def save(self, user, recipe):
        return self.as_user(user).post(URL, {"recipe_id": recipe.pk}, format="json")


class SaveTests(SavedRecipeTestCase):
    def test_save_a_recipe(self):
        response = self.save(self.alice, self.bibimbap)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(set(response.data), {"id", "recipe", "created_at"})
        self.assertEqual(response.data["recipe"]["id"], self.bibimbap.pk)
        self.assertEqual(response.data["recipe"]["name"], "Bibimbap")
        self.assertEqual(response.data["recipe"]["tags"][0]["name"], "Korean")
        saved = SavedRecipe.objects.get()
        self.assertEqual((saved.user, saved.recipe), (self.alice, self.bibimbap))

    def test_saving_twice_does_not_duplicate(self):
        first = self.save(self.alice, self.bibimbap)
        second = self.save(self.alice, self.bibimbap)

        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(second.data["id"], first.data["id"])
        self.assertEqual(SavedRecipe.objects.count(), 1)

    def test_two_users_can_save_the_same_recipe(self):
        self.save(self.alice, self.bibimbap)
        self.assertEqual(self.save(self.bob, self.bibimbap).status_code, status.HTTP_201_CREATED)
        self.assertEqual(SavedRecipe.objects.count(), 2)

    def test_user_comes_from_authentication_not_the_body(self):
        self.as_user(self.alice).post(
            URL, {"recipe_id": self.bibimbap.pk, "user": self.bob.pk, "user_id": self.bob.pk}, format="json"
        )
        self.assertEqual(SavedRecipe.objects.get().user, self.alice)

    def test_unknown_or_missing_recipe(self):
        for body in [{"recipe_id": 999999}, {"recipe_id": "abc"}, {}]:
            with self.subTest(body=body):
                response = self.as_user(self.alice).post(URL, body, format="json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("recipe_id", response.data)
        self.assertFalse(SavedRecipe.objects.exists())

    def test_deleting_a_recipe_removes_it_from_saved_lists(self):
        self.save(self.alice, self.pancakes)
        self.pancakes.delete()
        self.assertFalse(SavedRecipe.objects.exists())


class ListTests(SavedRecipeTestCase):
    def test_lists_only_your_own_newest_first(self):
        self.save(self.alice, self.bibimbap)
        self.save(self.alice, self.pancakes)
        self.save(self.bob, self.bibimbap)

        response = self.as_user(self.alice).get(URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(
            [item["recipe"]["name"] for item in response.data["results"]], ["Pancakes", "Bibimbap"]
        )
        bob = self.as_user(self.bob).get(URL)
        self.assertEqual([item["recipe"]["name"] for item in bob.data["results"]], ["Bibimbap"])

    def test_empty_list(self):
        response = self.as_user(self.alice).get(URL)
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["results"], [])

    def test_check_one_recipe(self):
        saved_id = self.save(self.alice, self.bibimbap).data["id"]

        saved = self.as_user(self.alice).get(URL, {"recipe_id": self.bibimbap.pk})
        self.assertEqual([item["id"] for item in saved.data["results"]], [saved_id])

        not_saved = self.as_user(self.alice).get(URL, {"recipe_id": self.pancakes.pk})
        self.assertEqual(not_saved.data["results"], [])

        bobs_view = self.as_user(self.bob).get(URL, {"recipe_id": self.bibimbap.pk})
        self.assertEqual(bobs_view.data["results"], [])

    def test_bad_recipe_filter(self):
        response = self.as_user(self.alice).get(URL, {"recipe_id": "abc"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_query_count_does_not_grow_with_the_list(self):
        def count_queries():
            with CaptureQueriesContext(connection) as queries:
                self.as_user(self.alice).get(URL)
            return len(queries)

        self.save(self.alice, self.bibimbap)
        small = count_queries()
        for index in range(8):
            recipe = Recipe.objects.create(name=f"Recipe {index}", instructions="Cook.")
            recipe.tags.add(self.korean)
            self.save(self.alice, recipe)
        self.assertEqual(count_queries(), small)


class RemoveTests(SavedRecipeTestCase):
    def test_remove_your_own(self):
        saved_id = self.save(self.alice, self.bibimbap).data["id"]

        response = self.as_user(self.alice).delete(f"{URL}{saved_id}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(SavedRecipe.objects.exists())
        self.assertTrue(Recipe.objects.filter(pk=self.bibimbap.pk).exists())

    def test_cannot_remove_someone_elses(self):
        saved_id = self.save(self.alice, self.bibimbap).data["id"]

        response = self.as_user(self.bob).delete(f"{URL}{saved_id}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(SavedRecipe.objects.filter(pk=saved_id).exists())

    def test_saving_again_after_removing(self):
        saved_id = self.save(self.alice, self.bibimbap).data["id"]
        self.as_user(self.alice).delete(f"{URL}{saved_id}/")
        self.assertEqual(self.save(self.alice, self.bibimbap).status_code, status.HTTP_201_CREATED)

    def test_no_editing_or_single_item_view(self):
        saved_id = self.save(self.alice, self.bibimbap).data["id"]
        client = self.as_user(self.alice)
        self.assertEqual(client.get(f"{URL}{saved_id}/").status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(
            client.patch(f"{URL}{saved_id}/", {}, format="json").status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )


class GuestTests(SavedRecipeTestCase):
    def test_guests_are_refused(self):
        saved_id = self.save(self.alice, self.bibimbap).data["id"]
        self.client.force_authenticate(None)

        self.assertIn(self.client.get(URL).status_code, GUEST_REFUSED)
        self.assertIn(
            self.client.post(URL, {"recipe_id": self.pancakes.pk}, format="json").status_code,
            GUEST_REFUSED,
        )
        self.assertIn(self.client.delete(f"{URL}{saved_id}/").status_code, GUEST_REFUSED)
        self.assertEqual(SavedRecipe.objects.count(), 1)
