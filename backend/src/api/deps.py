from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.api.auth import TokenVerifier

security = HTTPBearer()
token_verifier = TokenVerifier()


async def decoded_jwt_token(
    auth: Annotated[HTTPAuthorizationCredentials, Depends(security)],
):
    try:
        return await token_verifier.decoded_token(auth.credentials)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401, detail="Invalid or expired token"
        )
