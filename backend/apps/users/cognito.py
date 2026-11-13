"""
Cognito access-token verification (Issue #68).

The React app signs people in with Cognito managed login and sends the Cognito
*access token* on API calls as ``Authorization: Bearer <token>``. This module
decides whether a token is genuine; ``authentication.py`` turns an accepted
token into a local user.

A token is accepted only if:
- it is a JWT signed with RS256 by one of the User Pool's signing keys
  (published at the pool's JWKS URL),
- ``iss`` is this User Pool,
- it hasn't expired,
- ``token_use`` is ``access`` (ID tokens and anything else are rejected),
- ``client_id`` is one of the app clients in COGNITO_APP_CLIENT_IDS.

Signing keys are downloaded once and cached per process. A token whose key ID
(``kid``) isn't cached causes one fresh download, so Cognito key rotation works
without a restart. Those extra downloads are limited to one per minute, so
junk tokens can't make the server hammer Cognito.

Tokens are never logged or echoed back to the client.
"""

import logging
import threading
import time
from dataclasses import dataclass

import jwt
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

ALGORITHM = "RS256"
REQUIRED_CLAIMS = ("exp", "iat", "iss", "sub", "token_use", "client_id")

JWKS_TIMEOUT_SECONDS = 5
JWKS_MAX_AGE_SECONDS = 60 * 60  # re-download the keys at least hourly
JWKS_MIN_REFETCH_SECONDS = 60  # at most one unknown-kid download per minute


class InvalidToken(Exception):
    """The token was rejected.

    ``reason`` is for server logs only. ``public_message`` is what the client sees.
    """

    def __init__(self, reason, public_message="Invalid token."):
        super().__init__(reason)
        self.reason = reason
        self.public_message = public_message


class SigningKeysUnavailable(Exception):
    """The User Pool's signing keys couldn't be downloaded."""


@dataclass(frozen=True)
class CognitoSettings:
    issuer: str
    jwks_url: str
    app_client_ids: frozenset


def get_cognito_settings():
    """Cognito settings from config/settings.py, or None if any are missing."""
    region = getattr(settings, "COGNITO_REGION", "")
    user_pool_id = getattr(settings, "COGNITO_USER_POOL_ID", "")
    app_client_ids = frozenset(getattr(settings, "COGNITO_APP_CLIENT_IDS", ()))
    if not (region and user_pool_id and app_client_ids):
        return None
    issuer = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"
    return CognitoSettings(
        issuer=issuer,
        jwks_url=f"{issuer}/.well-known/jwks.json",
        app_client_ids=app_client_ids,
    )


def _clock():
    return time.monotonic()


class SigningKeyCache:
    """The User Pool's public signing keys, keyed by ``kid``."""

    def __init__(self, jwks_url):
        self.jwks_url = jwks_url
        self._keys = None
        self._fetched_at = None
        self._lock = threading.Lock()

    def get(self, kid):
        """The key for ``kid``, or None if the User Pool doesn't have it."""
        with self._lock:
            now = _clock()
            if self._keys is None or now - self._fetched_at >= JWKS_MAX_AGE_SECONDS:
                self._refresh(now)
            elif kid not in self._keys and now - self._fetched_at >= JWKS_MIN_REFETCH_SECONDS:
                # Possibly a key Cognito rotated in since the last download.
                self._refresh(now)
            return self._keys.get(kid)

    def _refresh(self, now):
        try:
            keys = self._download()
        except SigningKeysUnavailable:
            if self._keys is None:
                raise
            # Keep using the keys we have and try again later.
            logger.warning("Could not refresh Cognito signing keys; using cached keys.")
            self._fetched_at = now
            return
        self._keys = keys
        self._fetched_at = now

    def _download(self):
        try:
            response = requests.get(self.jwks_url, timeout=JWKS_TIMEOUT_SECONDS)
            response.raise_for_status()
            jwks = response.json()
        except (requests.RequestException, ValueError) as exc:
            logger.warning(
                "Could not download Cognito signing keys (%s).", exc.__class__.__name__
            )
            raise SigningKeysUnavailable from exc

        keys = {}
        entries = jwks.get("keys") if isinstance(jwks, dict) else None
        for entry in entries if isinstance(entries, list) else []:
            if not isinstance(entry, dict):
                continue
            kid = entry.get("kid")
            if not isinstance(kid, str) or not kid or entry.get("kty") != "RSA":
                continue
            if entry.get("use", "sig") != "sig":
                continue
            try:
                keys[kid] = jwt.PyJWK(entry, algorithm=ALGORITHM).key
            except (jwt.PyJWKError, jwt.InvalidKeyError, ValueError, TypeError, KeyError):
                logger.warning("Skipped an unusable key in the Cognito JWKS.")
        if not keys:
            logger.warning("The Cognito JWKS had no usable signing keys.")
            raise SigningKeysUnavailable
        return keys


_caches = {}
_caches_lock = threading.Lock()


def _signing_key_cache(jwks_url):
    with _caches_lock:
        cache = _caches.get(jwks_url)
        if cache is None:
            cache = _caches[jwks_url] = SigningKeyCache(jwks_url)
        return cache


def clear_signing_key_cache():
    """Forget all downloaded keys. Used by tests."""
    with _caches_lock:
        _caches.clear()


def verify_access_token(token, cognito):
    """The verified claims of a Cognito access token.

    Raises InvalidToken if the token is rejected, or SigningKeysUnavailable if
    the keys needed to check it can't be downloaded.
    """
    try:
        header = jwt.get_unverified_header(token)
    except jwt.InvalidTokenError as exc:
        raise InvalidToken("malformed token") from exc

    # Only RS256 is accepted. This also blocks "alg": "none" and HS256 tokens
    # that try to use the public key as a shared secret.
    if header.get("alg") != ALGORITHM:
        raise InvalidToken("unsupported signing algorithm")
    kid = header.get("kid")
    if not isinstance(kid, str) or not kid:
        raise InvalidToken("missing key ID")

    key = _signing_key_cache(cognito.jwks_url).get(kid)
    if key is None:
        raise InvalidToken("signed with a key the User Pool doesn't have")

    try:
        claims = jwt.decode(
            token,
            key=key,
            algorithms=[ALGORITHM],
            issuer=cognito.issuer,
            # Cognito access tokens have no "aud"; the app client is checked
            # through "client_id" below instead.
            options={"require": list(REQUIRED_CLAIMS), "verify_aud": False},
        )
    except jwt.ExpiredSignatureError as exc:
        raise InvalidToken("expired", "Token has expired.") from exc
    except jwt.InvalidIssuerError as exc:
        raise InvalidToken("issued by a different User Pool") from exc
    except jwt.InvalidTokenError as exc:
        raise InvalidToken(f"failed verification ({exc.__class__.__name__})") from exc

    if claims["token_use"] != "access":
        raise InvalidToken("not an access token")
    client_id = claims["client_id"]
    if not isinstance(client_id, str) or client_id not in cognito.app_client_ids:
        raise InvalidToken("issued to an app client that isn't allowed")
    subject = claims["sub"]
    if not isinstance(subject, str) or not subject or len(subject) > 255:
        raise InvalidToken("invalid subject")
    return claims
