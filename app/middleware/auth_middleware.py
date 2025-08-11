from typing import Optional, Set
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import jwt
from app.core.config import settings  # SECRET_KEY, y opcional: JWT_* vars

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

def _decode_jwt(token: str) -> dict:
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

def _extract_token(request: Request) -> Optional[str]:
    # 1) Authorization: Bearer
    auth_header = (request.headers.get("Authorization") or "").strip()
    if auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip()
    # 2) Cookie (emitido por Django)
    cookie_name = getattr(settings, "AUTH_COOKIE_NAME", "access_token")
    return request.cookies.get(cookie_name)

class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        api_prefix: str = "/api/v1",
        exempt_paths: Optional[Set[str]] = None,
        protected_methods: Optional[Set[str]] = None,
    ):
        super().__init__(app)
        self.api_prefix = api_prefix
        base_exempt = {
            "/",
            f"{self.api_prefix}/health",
            f"{self.api_prefix}/docs",
            f"{self.api_prefix}/redoc",
            f"{self.api_prefix}/openapi.json",
            # agrega aquí otros públicos (p. ej. _debug/echo) si corresponde
        }
        self.exempt_paths = base_exempt if exempt_paths is None else base_exempt | set(exempt_paths)
        # Por diseño protegemos métodos de escritura; para GET usa Depends si quieres requerir auth
        self.protected_methods = protected_methods or {"POST", "PUT", "PATCH", "DELETE"}

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method

        if path in self.exempt_paths or method == "OPTIONS":
            return await call_next(request)

        if method in self.protected_methods:
            token = _extract_token(request)
            if not token:
                return JSONResponse({"detail": "Authorization token required"}, status_code=401)

            try:
                payload = _decode_jwt(token)
            except jwt.ExpiredSignatureError:
                return JSONResponse({"detail": "Token expired"}, status_code=401)
            except jwt.InvalidTokenError:
                return JSONResponse({"detail": "Invalid token"}, status_code=403)

            # deja claims disponibles a vistas/routers
            request.state.user = payload
            request.state.user_id = payload.get("user_id") or payload.get("sub")

        return await call_next(request)
