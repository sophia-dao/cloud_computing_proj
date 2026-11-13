"""
Test helpers for Cognito sign-in (Issue #68). Only tests import this module.

FakeUserPool stands in for a Cognito User Pool. It signs access tokens with
throwaway RSA keys generated when the tests run, and answers the JWKS download
that cognito.py makes, so tests never contact AWS. Nothing here is a real
credential.
"""

import time
import uuid
from functools import lru_cache
from unittest import mock

import jwt
import requests
from cryptography.hazmat.primitives.asymmetric import rsa
from django.test import override_settings

from . import cognito

REGION = "us-east-1"
USER_POOL_ID = "us-east-1_TestPool"
APP_CLIENT_ID = "test-app-client"
ISSUER = f"https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}"
JWKS_URL = f"{ISSUER}/.well-known/jwks.json"

OTHER_ISSUER = f"https://cognito-idp.{REGION}.amazonaws.com/{REGION}_SomeOtherPool"

# Leave a claim out of a token: pool.token(exp=OMIT)
OMIT = object()


@lru_cache(maxsize=None)
def throwaway_key(name):
    """An RSA private key made once per test run (key generation is slow)."""
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


class FakeUserPool:
    def __init__(self):
        self.signing_keys = {"key-1": throwaway_key("key-1")}
        self.jwks_downloads = 0
        self.available = True

    def jwks(self):
        keys = []
        for kid, private_key in self.signing_keys.items():
            public_jwk = jwt.algorithms.RSAAlgorithm.to_jwk(private_key.public_key(), as_dict=True)
            keys.append({**public_jwk, "kid": kid, "alg": "RS256", "use": "sig"})
        return {"keys": keys}

    def _get(self, url, timeout=None):
        assert url == JWKS_URL, url
        self.jwks_downloads += 1
        if not self.available:
            raise requests.ConnectionError("fake Cognito is down")
        response = mock.Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = self.jwks()
        return response

    def patch_downloads(self):
        return mock.patch.object(cognito.requests, "get", side_effect=self._get)

    def claims(self, sub, **overrides):
        now = int(time.time())
        claims = {
            "sub": sub,
            "iss": ISSUER,
            "client_id": APP_CLIENT_ID,
            "token_use": "access",
            "scope": "openid email profile",
            "auth_time": now,
            "iat": now,
            "exp": now + 3600,
            "jti": str(uuid.uuid4()),
            "username": f"google_{sub}",
        }
        claims.update(overrides)
        return {name: value for name, value in claims.items() if value is not OMIT}

    def token(self, sub="sub-alice", *, kid="key-1", signing_key=None, **claim_overrides):
        """A signed access token. Pass claim=OMIT to leave a claim out."""
        return jwt.encode(
            self.claims(sub, **claim_overrides),
            signing_key or self.signing_keys[kid],
            algorithm="RS256",
            headers={"kid": kid},
        )


class CognitoTestMixin:
    """Fake User Pool + Cognito settings for every test in the class.

    self.pool is the fake pool. self.bearer(token) gives the request header.
    """

    def setUp(self):
        super().setUp()
        cognito.clear_signing_key_cache()
        self.addCleanup(cognito.clear_signing_key_cache)
        self.pool = FakeUserPool()
        self.enterContext(self.pool.patch_downloads())
        self.enterContext(
            override_settings(
                COGNITO_REGION=REGION,
                COGNITO_USER_POOL_ID=USER_POOL_ID,
                COGNITO_APP_CLIENT_IDS=[APP_CLIENT_ID],
            )
        )

    @staticmethod
    def bearer(token):
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def sign_in_as(self, sub):
        """Send every following request in this test with a valid token for `sub`."""
        self.client.credentials(**self.bearer(self.pool.token(sub)))
