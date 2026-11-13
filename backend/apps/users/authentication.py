"""
DRF authentication with Cognito access tokens (Issue #68).

Every API request is either:
- a guest request: no ``Authorization: Bearer`` header. Public endpoints work,
  protected ones answer 401.
- a signed-in request: a Cognito access token that passes cognito.py's checks.
  ``request.user`` is the Django auth user linked to the person's application
  User, so existing ownership code (inventory, recipes, profile) keeps working.

A bearer token that fails any check is a 401, never a silent guest request.
The frontend relies on that 401 to refresh the token and retry.

Cognito is the only way to sign in on the deployed site. The one exception is
DevBasicAuthentication below: a local-development shortcut that is switched off
unless a developer turns it on, and that never works when DEBUG is off.
"""

import hashlib
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from rest_framework import exceptions
from rest_framework.authentication import (
    BaseAuthentication,
    BasicAuthentication,
    get_authorization_header,
)

from .cognito import (
    InvalidToken,
    SigningKeysUnavailable,
    get_cognito_settings,
    verify_access_token,
)
from .models import User, UserProfile

logger = logging.getLogger(__name__)

# Same wording as the users views use for suspended accounts.
INACTIVE_ACCOUNT_MESSAGE = "This account is suspended or disabled."


class AuthenticationUnavailable(exceptions.APIException):
    status_code = 503
    default_detail = "Sign-in can't be checked right now. Please try again shortly."
    default_code = "authentication_unavailable"


class CognitoAccessTokenAuthentication(BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        parts = get_authorization_header(request).split()
        if not parts or parts[0].lower() != self.keyword.lower().encode():
            return None  # no bearer token: a guest request
        if len(parts) != 2:
            raise exceptions.AuthenticationFailed(
                "Invalid Authorization header. Expected 'Bearer <access token>'."
            )
        try:
            token = parts[1].decode("ascii")
        except UnicodeDecodeError:
            raise exceptions.AuthenticationFailed("Invalid token.") from None

        cognito = get_cognito_settings()
        if cognito is None:
            logger.error(
                "Rejected a bearer token because Cognito isn't configured. "
                "Set COGNITO_REGION, COGNITO_USER_POOL_ID and COGNITO_APP_CLIENT_IDS."
            )
            raise exceptions.AuthenticationFailed("Invalid token.")

        try:
            claims = verify_access_token(token, cognito)
        except InvalidToken as exc:
            level = logging.INFO if exc.reason == "expired" else logging.WARNING
            logger.log(level, "Rejected Cognito access token: %s.", exc.reason)
            raise exceptions.AuthenticationFailed(exc.public_message) from None
        except SigningKeysUnavailable:
            raise AuthenticationUnavailable() from None

        application_user = get_or_create_cognito_user(claims["iss"], claims["sub"])
        if (
            application_user.account_status != User.AccountStatus.ACTIVE
            or not application_user.auth_user.is_active
        ):
            raise exceptions.PermissionDenied(INACTIVE_ACCOUNT_MESSAGE)

        return (application_user.auth_user, claims)

    def authenticate_header(self, request):
        # Makes DRF answer 401 (not 403) when a protected endpoint has no valid token.
        return f'{self.keyword} realm="api"'


class DevBasicAuthentication(BasicAuthentication):
    """Local-development login shortcut: Django username + password over HTTP Basic.

    This is what the frontend's VITE_DEV_BASIC_AUTH (PR #72) sends, so
    logged-in pages can be tried without Cognito. It does nothing unless both
    DEBUG and DEV_BASIC_AUTH are True. Both are checked on every request, so
    it can't be switched on in production, where DEBUG is off, or during tests.
    """

    def authenticate(self, request):
        if not (settings.DEBUG and getattr(settings, "DEV_BASIC_AUTH", False)):
            return None
        return super().authenticate(request)


def _find_cognito_user(issuer, subject):
    return (
        User.objects.select_related("auth_user")
        .filter(cognito_issuer=issuer, cognito_subject=subject)
        .first()
    )


def _username_for(subject):
    # Django needs a unique username. Nobody types it; it just makes accounts
    # easy to spot in the Django admin.
    username = f"cognito_{subject}"
    if len(username) > 150:
        username = "cognito_" + hashlib.sha256(subject.encode()).hexdigest()
    return username


def get_or_create_cognito_user(issuer, subject):
    """The application User for a verified Cognito identity, created on first sign-in.

    A person is identified by the (issuer, sub) pair: which User Pool vouched
    for them, and Cognito's permanent ID for them in that pool. Email is never
    used to find or link accounts. It can change, and Cognito access tokens
    don't carry it anyway.

    First sign-in creates, in one transaction: a Django auth user with no
    usable password (so it can't be used for a password login), the
    application User, and an empty UserProfile.
    """
    application_user = _find_cognito_user(issuer, subject)
    if application_user is not None:
        return application_user

    try:
        with transaction.atomic():
            auth_user = get_user_model().objects.create_user(username=_username_for(subject))
            application_user = User.objects.create(
                auth_user=auth_user,
                cognito_issuer=issuer,
                cognito_subject=subject,
            )
            UserProfile.objects.create(user=application_user)
    except IntegrityError:
        # Usually two first requests from the same person at once: the other
        # one created the account, so use it.
        application_user = _find_cognito_user(issuer, subject)
        if application_user is None:
            # Something else already holds this sub or username. Never link it.
            logger.error("A Cognito identity conflicts with an existing account; not linking it.")
            raise exceptions.AuthenticationFailed(
                "This sign-in can't be linked to an account."
            ) from None
        return application_user

    logger.info("Created application User #%s on first Cognito sign-in.", application_user.pk)
    return application_user
