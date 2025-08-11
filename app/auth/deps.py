from typing import Annotated, Any, Dict, Optional
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from app.core.config import settings

bearer = HTTPBearer(auto_error=False)

def _jwt_key_and_alg() -> tuple[str, str]:
    alg: str = getattr(settings, "JWT_ALGORITHM", getattr(settings, "JWT_ALG", "HS256"))
    if alg.upper().startswith("RS"):
        key = getattr(settings, "JWT_PUBLIC_KEY", None) or getattr(settings, "JWT_KEY", None)
        if not key:
            raise RuntimeError("JWT_PUBLIC_KEY requerido para algoritmos RS*")
    else:
        key = getattr(settings, "SECRET_KEY", None)
        if not key:
            raise RuntimeError("SECRET_KEY requerido para algoritmos HS*")
    return key, alg

def _decode_jwt(token: str) -> Dict[str, Any]:
    key, alg = _jwt_key_and_alg()
    kwargs = {
        "algorithms": [alg],
        "options": {"require": ["exp"]},
        "leeway": getattr(settings, "JWT_LEEWAY", 10),
    }
    aud = getattr(settings, "JWT_AUDIENCE", None)
    iss = getattr(settings, "JWT_ISSUER", None)
    if aud:
        kwargs["audience"] = aud
    if iss:
        kwargs["issuer"] = iss
    return jwt.decode(token, key, **kwargs)

def _extract_token(request: Request, creds: Optional[HTTPAuthorizationCredentials]) -> Optional[str]:
    if creds and (creds.scheme or "").lower() == "bearer" and creds.credentials:
        return creds.credentials
    cookie_name = getattr(settings, "AUTH_COOKIE_NAME", "access_token")
    return request.cookies.get(cookie_name)

def get_current_user(
    request: Request,
    creds: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer)],
) -> Dict[str, Any]:
    token = _extract_token(request, creds)
    if not token:
        raise HTTPException(status_code=401, detail="Authorization token required")
    try:
        return _decode_jwt(token)  # dict con claims (id/sub, roles, etc.)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=403, detail="Invalid token")
