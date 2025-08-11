# app/auth/verify_token.py
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings

# Acepta Authorization: Bearer <token>; si no viene, intentará cookie HttpOnly (access_token)
security = HTTPBearer(auto_error=False)

def _jwt_key_and_alg() -> Tuple[str, str]:
    """
    Obtiene clave y algoritmo desde settings.
    HS* usa SECRET_KEY; RS* usa JWT_PUBLIC_KEY.
    """
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
    kwargs: Dict[str, Any] = {
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
    # 1) Authorization: Bearer
    if creds and (creds.scheme or "").lower() == "bearer" and creds.credentials:
        return creds.credentials
    # 2) Cookie HttpOnly (opcional)
    cookie_name = getattr(settings, "AUTH_COOKIE_NAME", "access_token")
    return request.cookies.get(cookie_name)

def verify_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """
    Dependencia para rutas y routers.
    - Extrae token de Authorization: Bearer o cookie.
    - Decodifica/valida JWT.
    - Normaliza a: {"id": ..., "role": ... , ...claims}
    Lanza 401/403 cuando corresponde.
    """
    token = _extract_token(request, credentials)
    if not token:
        raise HTTPException(status_code=401, detail="Authorization token required")

    try:
        claims = _decode_jwt(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=403, detail="Invalid token")

    uid = claims.get("id") or claims.get("user_id") or claims.get("sub")
    if uid is None:
        raise HTTPException(status_code=401, detail="Invalid token: user id missing")

    try:
        uid = int(uid)
    except Exception:
        # si viene como string no numérico, lo dejamos tal cual
        pass

    role = claims.get("role") or claims.get("rol") or claims.get("scope")

    normalized = dict(claims)
    normalized["id"] = uid
    normalized["role"] = role
    return normalized
