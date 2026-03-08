import jwt

from src.config import APISettings


class TokenVerifier:
    def __init__(self, settings: APISettings | None = None) -> None:
        self.settings = APISettings()
        self.jwks_client = jwt.PyJWKClient(self.settings.JKWS_URI)

    async def decoded_token(self, token: str) -> dict:
        signing_key = self.jwks_client.get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=self.settings.JWT_ALGORITHMS,
            options={"verify_aud": False},
        )
