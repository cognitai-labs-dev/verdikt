import datetime
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from src.api.auth import TokenVerifier
from src.config import APISettings

ISSUER = "https://issuer.example.com"
AUDIENCE = "test-client-id"


def _make_verifier(private_key) -> TokenVerifier:
    # Arrange: a verifier wired to a fake JWKS client that returns the
    # public key matching `private_key` — no network, no real JWKS fetch.
    settings = APISettings(
        OIDC_ISSUER=ISSUER,
        OIDC_AUDIENCE=AUDIENCE,
        OIDC_JWKS_URI="https://issuer.example.com/keys",
    )
    verifier = TokenVerifier(settings)
    signing_key = SimpleNamespace(key=private_key.public_key())
    verifier._jwks_client = SimpleNamespace(
        get_signing_key_from_jwt=lambda token: signing_key
    )
    return verifier


def _mint_token(private_key, *, issuer=ISSUER, audience=AUDIENCE, expired=False):
    now = datetime.datetime.now(datetime.timezone.utc)
    exp = now - datetime.timedelta(hours=1) if expired else now + datetime.timedelta(hours=1)
    claims = {
        "iss": issuer,
        "aud": audience,
        "sub": "user-123",
        "email": "person@example.com",
        "iat": now,
        "exp": exp,
    }
    return jwt.encode(claims, private_key, algorithm="RS256")


@pytest.fixture
def private_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.mark.anyio
async def test_decoded_token_valid_issuer_and_audience_returns_claims(private_key):
    # Arrange
    verifier = _make_verifier(private_key)
    token = _mint_token(private_key)

    # Act
    claims = await verifier.decoded_token(token)

    # Assert
    assert claims["sub"] == "user-123"
    assert claims["email"] == "person@example.com"


@pytest.mark.anyio
async def test_decoded_token_wrong_issuer_raises(private_key):
    # Arrange
    verifier = _make_verifier(private_key)
    token = _mint_token(private_key, issuer="https://evil.example.com")

    # Act / Assert
    with pytest.raises(jwt.InvalidIssuerError):
        await verifier.decoded_token(token)


@pytest.mark.anyio
async def test_decoded_token_wrong_audience_raises(private_key):
    # Arrange
    verifier = _make_verifier(private_key)
    token = _mint_token(private_key, audience="other-client-id")

    # Act / Assert
    with pytest.raises(jwt.InvalidAudienceError):
        await verifier.decoded_token(token)


@pytest.mark.anyio
async def test_decoded_token_expired_raises(private_key):
    # Arrange
    verifier = _make_verifier(private_key)
    token = _mint_token(private_key, expired=True)

    # Act / Assert
    with pytest.raises(jwt.ExpiredSignatureError):
        await verifier.decoded_token(token)
