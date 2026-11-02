
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient

from .models import (
    User,
    UserProfile,
    Tag,
    Allergen,
    UserPreference,
    UserAllergy,
)


class UserAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        AuthUser = get_user_model()

        self.auth_user = AuthUser.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="TestPassword123!",
        )

        self.user = User.objects.create(
            auth_user=self.auth_user,
        )

        UserProfile.objects.create(
            user=self.user,
            display_name="Test User",
        )

        self.other_auth_user = AuthUser.objects.create_user(
            username="otheruser",
            password="TestPassword123!",
        )

        self.other_user = User.objects.create(
            auth_user=self.other_auth_user,
        )

        UserProfile.objects.create(
            user=self.other_user,
            display_name="Other User",
        )

        self.tag1 = Tag.objects.create(
            name="Vegetarian",
            type=Tag.TagType.DIET,
        )

        self.tag2 = Tag.objects.create(
            name="Vietnamese",
            type=Tag.TagType.CUISINE,
        )

        self.allergen1 = Allergen.objects.create(
            name="Peanut",
        )

        self.allergen2 = Allergen.objects.create(
            name="Milk",
        )

        self.profile_url = reverse("current-user")
        self.preferences_url = reverse("current-user-preferences")
        self.allergies_url = reverse("current-user-allergies")

        self.client.force_authenticate(user=self.auth_user)

    def test_get_profile(self):
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.user.id)
        self.assertEqual(response.data["display_name"], "Test User")
        self.assertEqual(response.data["email"], "test@example.com")

    def test_update_profile(self):
        response = self.client.patch(
            self.profile_url,
            {"display_name": "Updated Name"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.user.profile.refresh_from_db()
        self.assertEqual(
            self.user.profile.display_name,
            "Updated Name",
        )

    def test_cannot_change_admin_status(self):
        response = self.client.patch(
            self.profile_url,
            {"is_admin": True, "cognito_subject": "fake"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_admin)
        self.assertIsNone(self.user.cognito_subject)

    def test_unauthenticated_requests_denied(self):
        self.client.force_authenticate(user=None)

        for url in [
            self.profile_url,
            self.preferences_url,
            self.allergies_url,
        ]:
            response = self.client.get(url)
            self.assertIn(response.status_code, [401, 403])

    def test_replace_preferences(self):
        response = self.client.put(
            self.preferences_url,
            {"tag_ids": [self.tag1.id, self.tag2.id]},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            UserPreference.objects.filter(user=self.user).count(),
            2,
        )

        response = self.client.put(
            self.preferences_url,
            {"tag_ids": [self.tag2.id]},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(
                UserPreference.objects.filter(
                    user=self.user
                ).values_list("tag_id", flat=True)
            ),
            [self.tag2.id],
        )

    def test_invalid_preference_ids(self):
        response = self.client.put(
            self.preferences_url,
            {"tag_ids": [999999]},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_duplicate_preference_ids(self):
        response = self.client.put(
            self.preferences_url,
            {"tag_ids": [self.tag1.id, self.tag1.id]},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_replace_allergies(self):
        response = self.client.put(
            self.allergies_url,
            {
                "allergen_ids": [
                    self.allergen1.id,
                    self.allergen2.id,
                ]
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            UserAllergy.objects.filter(user=self.user).count(),
            2,
        )

        response = self.client.put(
            self.allergies_url,
            {"allergen_ids": [self.allergen1.id]},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(
                UserAllergy.objects.filter(
                    user=self.user
                ).values_list("allergen_id", flat=True)
            ),
            [self.allergen1.id],
        )

    def test_invalid_allergen_ids(self):
        response = self.client.put(
            self.allergies_url,
            {"allergen_ids": [999999]},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_user_isolation(self):
        UserPreference.objects.create(
            user=self.other_user,
            tag=self.tag1,
        )

        UserAllergy.objects.create(
            user=self.other_user,
            allergen=self.allergen1,
        )

        preferences = self.client.get(self.preferences_url)
        allergies = self.client.get(self.allergies_url)

        self.assertEqual(preferences.data["preferences"], [])
        self.assertEqual(allergies.data["allergies"], [])

        self.client.put(
            self.preferences_url,
            {"tag_ids": [self.tag2.id]},
            format="json",
        )

        self.client.put(
            self.allergies_url,
            {"allergen_ids": [self.allergen2.id]},
            format="json",
        )

        self.assertTrue(
            UserPreference.objects.filter(
                user=self.other_user,
                tag=self.tag1,
            ).exists()
        )

        self.assertTrue(
            UserAllergy.objects.filter(
                user=self.other_user,
                allergen=self.allergen1,
            ).exists()
        )

    def test_suspended_user_denied(self):
        self.user.account_status = User.AccountStatus.SUSPENDED
        self.user.save()

        for url in [
            self.profile_url,
            self.preferences_url,
            self.allergies_url,
        ]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 403)

    def test_disabled_user_denied(self):
        self.user.account_status = User.AccountStatus.DISABLED
        self.user.save()

        for url in [
            self.profile_url,
            self.preferences_url,
            self.allergies_url,
        ]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 403)
