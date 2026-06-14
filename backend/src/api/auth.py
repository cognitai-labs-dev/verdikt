import json
from urllib.request import urlopen

import jwt

from src.config import APISettings


class TokenVerifier:
    def __init__(self, settings: APISettings | None = None) -> None:
        self.settings = settings or APISettings()
        self._jwks_client: jwt.PyJWKClient | None = None

    def _resolve_jwks_uri(self) -> str:
        if self.settings.OIDC_JWKS_URI:
            return self.settings.OIDC_JWKS_URI
        # Discover the JWKS URI from the issuer's OIDC discovery document.
        discovery_url = (
            f"{self.settings.OIDC_ISSUER.rstrip('/')}"
            "/.well-known/openid-configuration"
        )
        with urlopen(discovery_url) as response:
            document = json.load(response)
        return document["jwks_uri"]

    @property
    def jwks_client(self) -> jwt.PyJWKClient:
        # Resolved lazily so a misconfigured/unreachable issuer fails on first
        # request rather than at import/startup time.
        if self._jwks_client is None:
            self._jwks_client = jwt.PyJWKClient(
                self._resolve_jwks_uri()
            )
        return self._jwks_client

    async def decoded_token(self, token: str) -> dict:
        signing_key = self.jwks_client.get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=self.settings.JWT_ALGORITHMS,
            issuer=self.settings.OIDC_ISSUER,
            audience=self.settings.OIDC_AUDIENCE,
            options={"verify_aud": True, "verify_iss": True},
        )
