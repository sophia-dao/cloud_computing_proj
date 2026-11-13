"""
Registered-user recipe submission (Issue #67): create, validation,
duplicate-name warning, image upload, guest rejection and owner/admin rules.
"""

import io
import shutil
import tempfile
from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase

from apps.ingredients.models import Ingredient
from apps.recipes import serializers as recipe_serializers
from apps.recipes.models import Recipe, RecipeIngredient, Tag
from apps.users.models import User

RECIPES_URL = "/api/recipes/"
DUPLICATES_URL = "/api/recipes/duplicates/"

# A guest gets 401 or 403 depending on which authentication class the project
# lists first; either way the request is refused.
GUEST_REFUSED = (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


def make_user(username, *, is_admin=False, is_staff=False, account_status=None):
    auth_user = get_user_model().objects.create_user(username=username, is_staff=is_staff)
    fields = {"auth_user": auth_user, "is_admin": is_admin}
    if account_status:
        fields["account_status"] = account_status
    User.objects.create(**fields)
    return auth_user


def image_file(name="photo.png", image_format="PNG", size=(8, 8)):
    buffer = io.BytesIO()
    Image.new("RGB", size, "orange").save(buffer, format=image_format)
    content_type = f"image/{image_format.lower()}"
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=content_type)


class SubmissionTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = make_user("alice")
        cls.bob = make_user("bob")
        cls.rice = Ingredient.objects.create(name="White Rice", allergens_verified=True)
        cls.kimchi = Ingredient.objects.create(name="Kimchi", allergens_verified=True)
        cls.egg = Ingredient.objects.create(name="Egg", allergens_verified=True)
        cls.korean = Tag.objects.create(name="Korean", type=Tag.TagType.CUISINE)
        cls.quick = Tag.objects.create(name="Quick", type=Tag.TagType.OTHER)

    def payload(self, **overrides):
        data = {
            "name": "Kimchi Fried Rice",
            "description": "Leftover rice, crispy and spicy.",
            "instructions": "Fry the kimchi, add rice, top with an egg.",
            "preparation_time": 10,
            "cooking_time": 15,
            "ingredients": [
                {"ingredient_id": self.rice.pk, "quantity": 2, "unit": "cup"},
                {"ingredient_id": self.kimchi.pk, "quantity": 0.5, "unit": "cup"},
                {"ingredient_id": self.egg.pk, "quantity": 1, "is_optional": True},
            ],
            "tag_ids": [self.korean.pk, self.quick.pk],
        }
        data.update(overrides)
        return data

    def create_as(self, user, **overrides):
        self.client.force_authenticate(user)
        response = self.client.post(RECIPES_URL, self.payload(**overrides), format="json")
        self.client.force_authenticate(None)
        return response


class CreateRecipeTests(SubmissionTestCase):
    def test_signed_in_user_creates_a_recipe(self):
        response = self.create_as(self.alice)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(pk=response.data["id"])
        self.assertEqual(recipe.owner, self.alice)
        self.assertEqual(recipe.preparation_time, 10)
        self.assertEqual(recipe.cooking_time, 15)
        self.assertEqual(
            list(recipe.recipe_ingredients.values_list("ingredient__name", "is_optional")),
            [("White Rice", False), ("Kimchi", False), ("Egg", True)],
        )
        self.assertEqual(set(recipe.tags.values_list("name", flat=True)), {"Korean", "Quick"})
        self.assertEqual(response.data["owner"], {"id": self.alice.pk})

    def test_new_recipe_appears_in_search_and_detail(self):
        recipe_id = self.create_as(self.alice).data["id"]

        search = self.client.get(RECIPES_URL, {"search": "kimchi fried"})
        self.assertIn(recipe_id, [item["id"] for item in search.data["results"]])

        detail = self.client.get(f"{RECIPES_URL}{recipe_id}/")
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(len(detail.data["ingredients"]), 3)

    def test_only_required_fields(self):
        response = self.create_as(
            self.alice,
            description="",
            preparation_time=None,
            cooking_time=None,
            tag_ids=[],
            ingredients=[{"ingredient_id": self.rice.pk}],
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_name_spacing_is_tidied(self):
        response = self.create_as(self.alice, name="  Kimchi   Fried  Rice ")
        self.assertEqual(response.data["name"], "Kimchi Fried Rice")

    def test_owner_cannot_be_chosen_by_the_client(self):
        response = self.create_as(self.alice, owner=self.bob.pk, owner_id=self.bob.pk)
        self.assertEqual(Recipe.objects.get(pk=response.data["id"]).owner, self.alice)

    def test_guest_cannot_create(self):
        response = self.client.post(RECIPES_URL, self.payload(), format="json")
        self.assertIn(response.status_code, GUEST_REFUSED)
        self.assertFalse(Recipe.objects.exists())


class ValidationTests(SubmissionTestCase):
    def assert_rejected(self, field, **overrides):
        response = self.create_as(self.alice, **overrides)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertIn(field, response.data)
        self.assertFalse(Recipe.objects.exists())

    def test_required_fields(self):
        for field in ["name", "instructions", "ingredients"]:
            with self.subTest(field=field):
                payload = self.payload()
                del payload[field]
                self.client.force_authenticate(self.alice)
                response = self.client.post(RECIPES_URL, payload, format="json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(field, response.data)

    def test_blank_name_and_instructions(self):
        self.assert_rejected("name", name="   ")
        self.assert_rejected("instructions", instructions="")

    def test_needs_at_least_one_ingredient(self):
        self.assert_rejected("ingredients", ingredients=[])

    def test_unknown_ingredient(self):
        self.assert_rejected("ingredients", ingredients=[{"ingredient_id": 999999}])

    def test_same_ingredient_twice(self):
        twice = [{"ingredient_id": self.rice.pk}, {"ingredient_id": self.rice.pk}]
        self.assert_rejected("ingredients", ingredients=twice)

    def test_amount_must_be_positive(self):
        self.assert_rejected(
            "ingredients", ingredients=[{"ingredient_id": self.rice.pk, "quantity": 0}]
        )

    def test_unknown_tag(self):
        self.assert_rejected("tag_ids", tag_ids=[999999])

    def test_times_cannot_be_negative(self):
        self.assert_rejected("cooking_time", cooking_time=-5)


class DuplicateNameTests(SubmissionTestCase):
    def setUp(self):
        self.existing_id = self.create_as(self.bob).data["id"]

    def check(self, name):
        return self.client.get(DUPLICATES_URL, {"name": name})

    def test_matches_ignore_case_and_extra_spaces(self):
        for name in ["Kimchi Fried Rice", "kimchi fried rice", "  KIMCHI   fried  Rice "]:
            with self.subTest(name=name):
                response = self.check(name)
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data["name"], " ".join(name.split()))
                self.assertEqual(
                    response.data["matches"],
                    [{"id": self.existing_id, "name": "Kimchi Fried Rice"}],
                )

    def test_different_names_do_not_match(self):
        for name in ["Kimchi Fried Rice Bowl", "Fried Rice", "Kimchi Rice"]:
            with self.subTest(name=name):
                self.assertEqual(self.check(name).data["matches"], [])

    def test_name_is_required(self):
        self.assertEqual(self.client.get(DUPLICATES_URL).status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.check("   ").status_code, status.HTTP_400_BAD_REQUEST)

    def test_only_a_warning_creating_still_works(self):
        response = self.create_as(self.alice, name="kimchi fried RICE")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(self.check("Kimchi Fried Rice").data["matches"]), 2)

    def test_number_of_matches_is_capped(self):
        for _ in range(7):
            self.create_as(self.alice)
        self.assertEqual(len(self.check("Kimchi Fried Rice").data["matches"]), 5)


class OwnerAndAdminTests(SubmissionTestCase):
    def setUp(self):
        self.recipe_id = self.create_as(self.alice).data["id"]
        self.url = f"{RECIPES_URL}{self.recipe_id}/"

    def patch_as(self, user, name="Renamed"):
        self.client.force_authenticate(user)
        return self.client.patch(self.url, {"name": name}, format="json")

    def delete_as(self, user):
        self.client.force_authenticate(user)
        return self.client.delete(self.url)

    def test_other_users_cannot_edit_or_delete(self):
        self.assertEqual(self.patch_as(self.bob).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.delete_as(self.bob).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Recipe.objects.get(pk=self.recipe_id).name, "Kimchi Fried Rice")

    def test_owner_can_edit_and_delete(self):
        self.assertEqual(self.patch_as(self.alice).status_code, status.HTTP_200_OK)
        self.assertEqual(self.delete_as(self.alice).status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(pk=self.recipe_id).exists())

    def test_guest_cannot_edit_or_delete(self):
        self.assertIn(self.client.patch(self.url, {"name": "x"}, format="json").status_code, GUEST_REFUSED)
        self.assertIn(self.client.delete(self.url).status_code, GUEST_REFUSED)

    def test_application_admin_can_edit_and_delete_any_recipe(self):
        admin = make_user("admin", is_admin=True)
        self.assertEqual(self.patch_as(admin).status_code, status.HTTP_200_OK)
        self.assertEqual(self.delete_as(admin).status_code, status.HTTP_204_NO_CONTENT)

    def test_django_staff_still_count_as_admin(self):
        staff = make_user("staff", is_staff=True)
        self.assertEqual(self.patch_as(staff).status_code, status.HTTP_200_OK)

    def test_suspended_admin_has_no_admin_rights(self):
        admin = make_user("old-admin", is_admin=True, account_status=User.AccountStatus.SUSPENDED)
        self.assertEqual(self.patch_as(admin).status_code, status.HTTP_403_FORBIDDEN)

    def test_user_without_application_account_is_not_admin(self):
        loose = get_user_model().objects.create_user(username="no-account")
        self.assertEqual(self.patch_as(loose).status_code, status.HTTP_403_FORBIDDEN)


class ImageUploadTests(SubmissionTestCase):
    def setUp(self):
        media_root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, media_root, ignore_errors=True)
        storages = {
            **settings.STORAGES,
            "default": {
                "BACKEND": "django.core.files.storage.FileSystemStorage",
                "OPTIONS": {"location": media_root, "base_url": "/media/"},
            },
        }
        self.enterContext(override_settings(STORAGES=storages, MEDIA_ROOT=media_root))
        self.recipe_id = self.create_as(self.alice).data["id"]
        self.url = f"{RECIPES_URL}{self.recipe_id}/image/"

    def upload_as(self, user, file):
        self.client.force_authenticate(user)
        return self.client.post(self.url, {"image": file}, format="multipart")

    def test_owner_uploads_an_image(self):
        response = self.upload_as(self.alice, image_file("my holiday photo.png"))

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        recipe = Recipe.objects.get(pk=self.recipe_id)
        self.assertTrue(recipe.image.name.startswith("recipes/"))
        self.assertTrue(recipe.image.name.endswith(".png"))
        self.assertNotIn("holiday", recipe.image.name)
        self.assertIn(recipe.image.name, response.data["image"])

        detail = self.client.get(f"{RECIPES_URL}{self.recipe_id}/")
        self.assertEqual(detail.data["image"], response.data["image"])

    def test_jpeg_and_webp_are_accepted(self):
        for image_format, extension in [("JPEG", ".jpg"), ("WEBP", ".webp")]:
            with self.subTest(image_format=image_format):
                response = self.upload_as(self.alice, image_file(image_format=image_format))
                self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
                self.assertTrue(Recipe.objects.get(pk=self.recipe_id).image.name.endswith(extension))

    def test_not_an_image(self):
        fake = SimpleUploadedFile("photo.jpg", b"definitely not an image", content_type="image/jpeg")
        response = self.upload_as(self.alice, fake)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("image", response.data)
        self.assertFalse(Recipe.objects.get(pk=self.recipe_id).image)

    def test_unsupported_format(self):
        response = self.upload_as(self.alice, image_file("anim.gif", image_format="GIF"))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_too_large(self):
        with mock.patch.object(recipe_serializers, "MAX_IMAGE_BYTES", 50):
            response = self.upload_as(self.alice, image_file(size=(64, 64)))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("MB or smaller", str(response.data["image"]))

    def test_missing_file(self):
        self.client.force_authenticate(self.alice)
        response = self.client.post(self.url, {}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_only_owner_or_admin_can_upload(self):
        self.assertEqual(self.upload_as(self.bob, image_file()).status_code, status.HTTP_403_FORBIDDEN)
        admin = make_user("admin", is_admin=True)
        self.assertEqual(self.upload_as(admin, image_file()).status_code, status.HTTP_200_OK)

    def test_guest_cannot_upload(self):
        response = self.client.post(self.url, {"image": image_file()}, format="multipart")
        self.assertIn(response.status_code, GUEST_REFUSED)
