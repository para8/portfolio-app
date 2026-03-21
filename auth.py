import os
from functools import lru_cache

import jwt
from jwt import PyJWKClient
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_bearer = HTTPBearer()


@lru_cache(maxsize=1)
def _jwks_client() -> PyJWKClient:
    """Cached JWKS client — fetches Supabase public keys once per Lambda instance."""
    url = os.environ["SUPABASE_URL"].strip().rstrip("/") + "/auth/v1/.well-known/jwks.json"
    return PyJWKClient(url)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> str:
    token = credentials.credentials
    try:
        signing_key = _jwks_client().get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256"],
            audience="authenticated",
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    uid = payload.get("sub")
    if not uid:
        raise HTTPException(
            status_code=401,
            detail="Missing sub claim",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return uid
