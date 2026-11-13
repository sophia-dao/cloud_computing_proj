"""
Tests for Cognito access-token authentication and GET /api/auth/me/ (Issue #68).

Tokens are signed by a fake User Pool (apps/users/testing.py) with keys made
when the tests run. No request ever goes to AWS.
"""

import logging
import time
from unittest import mock

import jwt
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework import exceptions, status
from rest_framework.test import APITestCase

from . import authentication, cognito
from .models import User, UserProfile
from .testing import (
    APP_CLIENT_ID,
    ISSUER,
    OMIT,
    OTHER_ISSUER,
    CognitoTestMixin,
    throwaway_key,
)

ME_URL = reverse("auth-me")
CONTRACT_FIELDS = {"id", "email", "display_name", "profile_image", "is_admin"}
# HTTP Basic for the made-up test user alice / a-test-password.
BASIC_ALICE = "Basic YWxpY2U6YS10ZXN0LXBhc3N3b3Jk"


class AccessTokenValidationTests(CognitoTestMixin, APITestCase):
    def assert_rejected(self, token, detail="Invalid token."):
        with self.assertLogs("apps.users", level="INFO") as logs:
            response = self.client.get(ME_URL, **self.bearer(token))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["detail"], detail)
        self.assertEqual(response["WWW-Authenticate"], 'Bearer realm="api"')
        self.assertFalse(User.objects.exists())
        return logs

    def test_valid_access_token_is_accepted(self):
        response = self.client.get(ME_URL, **self.bearer(self.pool.token("sub-alice")))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["id"], User.objects.get(cognito_subject="sub-alice").pk
        )

    def test_expired_token(self):
        now = int(time.time())
        token = self.pool.token(iat=now - 3700, exp=now - 100)
        self.assert_rejected(token, detail="Token has expired.")

    def test_malformed_tokens(self):
        for token in ["not-a-jwt", "a.b.c", "eyJhbGciOiJSUzI1NiJ9.e30"]:
            with self.subTest(token=token):
                self.assert_rejected(token)

    def test_tampered_payload_fails_signature_check(self):
        header, payload, signature = self.pool.token().split(".")
        forged = jwt.utils.base64url_encode(
            b'{"sub":"sub-mallory","iss":"%s","client_id":"%s","token_use":"access",'
            b'"iat":1,"exp":9999999999}' % (ISSUER.encode(), APP_CLIENT_ID.encode())
        ).decode()
        self.assert_rejected(f"{header}.{forged}.{signature}")

    def test_wrong_issuer(self):
        self.assert_rejected(self.pool.token(iss=OTHER_ISSUER))

    def test_wrong_app_client(self):
        self.assert_rejected(self.pool.token(client_id="some-other-app-client"))

    def test_client_id_that_is_not_a_string(self):
        self.assert_rejected(self.pool.token(client_id=[APP_CLIENT_ID]))

    def test_id_token_is_not_an_access_token(self):
        id_token = self.pool.token(token_use="id", aud=APP_CLIENT_ID, client_id=OMIT)
        self.assert_rejected(id_token)
        self.assert_rejected(self.pool.token(token_use="id"))

    def test_token_signed_by_a_key_outside_the_pool(self):
        self.assert_rejected(self.pool.token(signing_key=throwaway_key("attacker")))

    def test_unsigned_and_symmetric_tokens(self):
        claims = self.pool.claims("sub-alice")
        unsigned = jwt.encode(claims, None, algorithm="none", headers={"kid": "key-1"})
        hs256 = jwt.encode(claims, "x" * 32, algorithm="HS256", headers={"kid": "key-1"})
        for token in [unsigned, hs256]:
            with self.subTest(token=token[:20]):
                self.assert_rejected(token)

    def test_token_without_key_id(self):
        claims = self.pool.claims("sub-alice")
        token = jwt.encode(claims, self.pool.signing_keys["key-1"], algorithm="RS256")
        self.assert_rejected(token)

    def test_each_required_claim(self):
        for claim in cognito.REQUIRED_CLAIMS:
            with self.subTest(claim=claim):
                self.assert_rejected(self.pool.token(**{claim: OMIT}))

    def test_empty_subject(self):
        self.assert_rejected(self.pool.token(sub=""))

    def test_badly_formed_authorization_headers(self):
        for header in ["Bearer", f"Bearer {self.pool.token()} extra"]:
            with self.subTest(header=header[:20]):
                response = self.client.get(ME_URL, HTTP_AUTHORIZATION=header)
                self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_scheme_is_case_insensitive(self):
        response = self.client.get(ME_URL, HTTP_AUTHORIZATION=f"bearer {self.pool.token()}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_no_token_means_guest(self):
        response = self.client.get(ME_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response["WWW-Authenticate"], 'Bearer realm="api"')

    def test_django_password_and_session_logins_are_not_accepted(self):
        get_user_model().objects.create_user(username="alice", password="a-test-password")

        basic = self.client.get(ME_URL, HTTP_AUTHORIZATION=BASIC_ALICE)
        self.assertEqual(basic.status_code, status.HTTP_401_UNAUTHORIZED)

        self.assertTrue(self.client.login(username="alice", password="a-test-password"))
        session = self.client.get(ME_URL)
        self.assertEqual(session.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_tokens_never_appear_in_logs_or_responses(self):
        token = self.pool.token(client_id="some-other-app-client")
        logs = self.assert_rejected(token)
        self.assertIn("issued to an app client that isn't allowed", logs.output[0])
        for line in logs.output:
            self.assertNotIn(token, line)
            self.assertNotIn(token.split(".")[1], line)

        with self.assertLogs("apps.users", level="INFO"):
            response = self.client.get(ME_URL, **self.bearer(token))
        self.assertNotIn(token.split(".")[1], response.content.decode())

    def test_without_cognito_settings_tokens_are_rejected_but_guests_work(self):
        with override_settings(COGNITO_USER_POOL_ID=""):
            with self.assertLogs("apps.users", level="ERROR"):
                response = self.client.get(ME_URL, **self.bearer(self.pool.token()))
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

            self.assertEqual(self.client.get("/api/tags/").status_code, status.HTTP_200_OK)
        self.assertEqual(self.pool.jwks_downloads, 0)


class SigningKeyTests(CognitoTestMixin, APITestCase):
    """JWKS download, caching and key rotation."""

    def setUp(self):
        super().setUp()
        self.now = 1_000_000.0
        self.enterContext(mock.patch.object(cognito, "_clock", lambda: self.now))

    def get_me(self, token):
        return self.client.get(ME_URL, **self.bearer(token))

    def test_keys_are_downloaded_once_and_cached(self):
        for sub in ["sub-alice", "sub-bob", "sub-alice"]:
            self.assertEqual(self.get_me(self.pool.token(sub)).status_code, 200)
        self.assertEqual(self.pool.jwks_downloads, 1)

    def test_rotated_in_key_is_picked_up_without_restart(self):
        self.assertEqual(self.get_me(self.pool.token(kid="key-1")).status_code, 200)

        self.pool.signing_keys["key-2"] = throwaway_key("key-2")
        self.now += cognito.JWKS_MIN_REFETCH_SECONDS
        response = self.get_me(self.pool.token(kid="key-2"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.pool.jwks_downloads, 2)

    def test_unknown_key_ids_cannot_force_repeated_downloads(self):
        stranger = throwaway_key("attacker")
        with self.assertLogs("apps.users", level="WARNING"):
            for _ in range(5):
                response = self.get_me(self.pool.token(kid="made-up", signing_key=stranger))
                self.assertEqual(response.status_code, 401)
        self.assertEqual(self.pool.jwks_downloads, 1)

        self.now += cognito.JWKS_MIN_REFETCH_SECONDS
        with self.assertLogs("apps.users", level="WARNING"):
            self.get_me(self.pool.token(kid="made-up", signing_key=stranger))
        self.assertEqual(self.pool.jwks_downloads, 2)

    def test_key_removed_from_the_pool_stops_working(self):
        self.assertEqual(self.get_me(self.pool.token(kid="key-1")).status_code, 200)

        self.pool.signing_keys = {"key-2": throwaway_key("key-2")}
        self.now += cognito.JWKS_MAX_AGE_SECONDS
        with self.assertLogs("apps.users", level="WARNING"):
            response = self.get_me(self.pool.token(kid="key-1", signing_key=throwaway_key("key-1")))
        self.assertEqual(response.status_code, 401)

    def test_cognito_unreachable_on_first_download(self):
        self.pool.available = False
        with self.assertLogs("apps.users", level="WARNING"):
            response = self.get_me(self.pool.token())
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

        self.pool.available = True
        self.assertEqual(self.get_me(self.pool.token()).status_code, 200)

    def test_cached_keys_keep_working_if_a_refresh_fails(self):
        self.assertEqual(self.get_me(self.pool.token()).status_code, 200)

        self.pool.available = False
        self.now += cognito.JWKS_MAX_AGE_SECONDS
        with self.assertLogs("apps.users", level="WARNING"):
            response = self.get_me(self.pool.token())
        self.assertEqual(response.status_code, 200)

    def test_bad_jwks_responses_are_not_trusted(self):
        for body in [{}, {"keys": []}, {"keys": [{"kid": "key-1", "kty": "RSA"}]}, ["nope"]]:
            with self.subTest(body=body):
                cognito.clear_signing_key_cache()
                with mock.patch.object(self.pool, "jwks", return_value=body):
                    with self.assertLogs("apps.users", level="WARNING"):
                        response = self.get_me(self.pool.token())
                self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)


class FirstSignInTests(CognitoTestMixin, APITestCase):
    """Mapping (issuer, sub) to a local User, and safe first-sign-in provisioning."""

    def get_me(self, sub, **claims):
        return self.client.get(ME_URL, **self.bearer(self.pool.token(sub, **claims)))

    def test_first_sign_in_creates_the_local_account(self):
        response = self.get_me("sub-alice")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user = User.objects.select_related("auth_user").get()
        self.assertEqual(user.cognito_issuer, ISSUER)
        self.assertEqual(user.cognito_subject, "sub-alice")
        self.assertEqual(user.account_status, User.AccountStatus.ACTIVE)
        self.assertFalse(user.is_admin)
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
        self.assertEqual(user.auth_user.username, "cognito_sub-alice")
        self.assertFalse(user.auth_user.has_usable_password())
        self.assertFalse(user.auth_user.is_staff)

    def test_later_sign_ins_reuse_the_same_account(self):
        first = self.get_me("sub-alice").data["id"]
        second = self.get_me("sub-alice").data["id"]
        self.assertEqual(first, second)
        self.assertEqual(User.objects.count(), 1)

    def test_different_people_get_different_accounts(self):
        alice = self.get_me("sub-alice").data["id"]
        bob = self.get_me("sub-bob").data["id"]
        self.assertNotEqual(alice, bob)

    def test_email_is_never_used_to_link_accounts(self):
        get_user_model().objects.create_user(username="existing", email="shared@example.com")
        alice = self.get_me("sub-alice", email="shared@example.com").data["id"]
        bob = self.get_me("sub-bob", email="shared@example.com").data["id"]
        self.assertNotEqual(alice, bob)
        self.assertEqual(User.objects.count(), 2)
        self.assertFalse(User.objects.filter(auth_user__username="existing").exists())

    def test_same_sub_from_another_pool_is_not_linked(self):
        self.get_me("sub-alice")
        with self.assertLogs("apps.users", level="ERROR"):
            with self.assertRaises(exceptions.AuthenticationFailed):
                authentication.get_or_create_cognito_user(OTHER_ISSUER, "sub-alice")
        self.assertEqual(User.objects.count(), 1)

    def test_two_first_requests_at_once_share_one_account(self):
        # Simulate another request creating the account between our lookup and insert.
        existing_id = self.get_me("sub-alice").data["id"]
        real_find = authentication._find_cognito_user
        with mock.patch.object(
            authentication, "_find_cognito_user", side_effect=[None, real_find(ISSUER, "sub-alice")]
        ):
            user = authentication.get_or_create_cognito_user(ISSUER, "sub-alice")
        self.assertEqual(user.pk, existing_id)
        self.assertEqual(User.objects.count(), 1)

    def test_suspended_and_disabled_accounts_are_refused(self):
        self.get_me("sub-alice")
        user = User.objects.get()
        for account_status in [User.AccountStatus.SUSPENDED, User.AccountStatus.DISABLED]:
            with self.subTest(account_status=account_status):
                User.objects.filter(pk=user.pk).update(account_status=account_status)
                # Inventory has no account-status check of its own, so this
                # proves the refusal happens at sign-in for every endpoint.
                for url in [ME_URL, "/api/inventory/"]:
                    response = self.client.get(url, **self.bearer(self.pool.token("sub-alice")))
                    self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
                    self.assertEqual(
                        response.data["detail"], authentication.INACTIVE_ACCOUNT_MESSAGE
                    )

    def test_deactivated_django_user_is_refused(self):
        self.get_me("sub-alice")
        get_user_model().objects.update(is_active=False)
        response = self.client.get("/api/inventory/", **self.bearer(self.pool.token("sub-alice")))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_comes_from_django_not_from_the_token(self):
        self.assertFalse(self.get_me("sub-alice", **{"cognito:groups": ["admin"]}).data["is_admin"])
        User.objects.update(is_admin=True)
        self.assertTrue(self.get_me("sub-alice").data["is_admin"])


class DevLoginShortcutTests(CognitoTestMixin, APITestCase):
    """The local-development Basic login (DJANGO_DEV_BASIC_AUTH) and its limits."""

    URL = "/api/inventory/"

    def setUp(self):
        super().setUp()
        get_user_model().objects.create_user(username="alice", password="a-test-password")
        # With DEBUG on, Django prints every 401 to the console. Keep test output clean.
        request_logger = logging.getLogger("django.request")
        self.addCleanup(request_logger.setLevel, request_logger.level)
        request_logger.setLevel(logging.ERROR)

    def get_with_basic(self, header=BASIC_ALICE):
        return self.client.get(self.URL, HTTP_AUTHORIZATION=header)

    @override_settings(DEBUG=True, DEV_BASIC_AUTH=True)
    def test_works_locally_when_switched_on(self):
        self.assertEqual(self.get_with_basic().status_code, status.HTTP_200_OK)

    @override_settings(DEBUG=True, DEV_BASIC_AUTH=True)
    def test_wrong_password_is_still_rejected(self):
        wrong = "Basic YWxpY2U6d3Jvbmc="  # alice / wrong
        self.assertEqual(self.get_with_basic(wrong).status_code, status.HTTP_401_UNAUTHORIZED)

    @override_settings(DEBUG=True, DEV_BASIC_AUTH=False)
    def test_off_unless_switched_on(self):
        self.assertEqual(self.get_with_basic().status_code, status.HTTP_401_UNAUTHORIZED)

    @override_settings(DEBUG=False, DEV_BASIC_AUTH=True)
    def test_never_works_with_debug_off(self):
        # Production runs with DEBUG off, so the switch can't open it up there.
        self.assertEqual(self.get_with_basic().status_code, status.HTTP_401_UNAUTHORIZED)

    @override_settings(DEBUG=True, DEV_BASIC_AUTH=True)
    def test_cognito_tokens_still_work_alongside_it(self):
        response = self.client.get(self.URL, **self.bearer(self.pool.token("sub-alice")))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        guest = self.client.get(self.URL)
        self.assertEqual(guest.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(guest["WWW-Authenticate"], 'Bearer realm="api"')


class AuthMeContractTests(CognitoTestMixin, APITestCase):
    """GET /api/auth/me/ response contract used by the frontend (#69, PR #74)."""

    def setUp(self):
        super().setUp()
        self.sign_in_as("sub-alice")

    def test_response_shape(self):
        response = self.client.get(ME_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data), CONTRACT_FIELDS)
        self.assertEqual(
            response.data,
            {
                "id": User.objects.get().pk,
                # Cognito access tokens carry no email, so a new account has none.
                # The frontend shows the ID token's email instead.
                "email": "",
                "display_name": "",
                "profile_image": None,
                "is_admin": False,
            },
        )

    def test_matches_users_me(self):
        self.assertEqual(self.client.get(ME_URL).data, self.client.get("/api/users/me/").data)

    def test_profile_edits_show_up(self):
        response = self.client.patch("/api/users/me/", {"display_name": "Alice"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get(ME_URL).data["display_name"], "Alice")

    def test_read_only(self):
        for method in ["post", "put", "patch", "delete"]:
            with self.subTest(method=method):
                response = getattr(self.client, method)(ME_URL, {}, format="json")
                self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
