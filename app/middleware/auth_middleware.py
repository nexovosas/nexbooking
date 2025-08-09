# app/middleware/auth_middleware.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import jwt
from app.core.config import settings  # solo para SECRET_KEY y otros claims

class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, api_prefix: str = "/api/v1",
                 exempt_paths: set[str] | None = None,
                 protected_methods: set[str] | None = None):
        super().__init__(app)
        self.api_prefix = api_prefix
        base_exempt = {
            "/",
            f"{self.api_prefix}/health",
            f"{self.api_prefix}/docs",
            f"{self.api_prefix}/openapi.json",
        }
        self.exempt_paths = base_exempt if exempt_paths is None else base_exempt | set(exempt_paths)
        self.protected_methods = protected_methods or {"POST", "PUT", "PATCH", "DELETE"}

    async def dispatch(self, request, call_next):
        path = request.url.path
        method = request.method

        if path in self.exempt_paths or method == "OPTIONS":
            return await call_next(request)

        if method in self.protected_methods:
            auth_header = (request.headers.get("Authorization") or "").strip()
            if not auth_header.lower().startswith("bearer "):
                return JSONResponse({"detail": "Authorization token required"}, status_code=401)

            token = auth_header.split(" ", 1)[1].strip()
            try:
                payload = jwt.decode(
                    token,
                    settings.SECRET_KEY,
                    algorithms=[getattr(settings, "JWT_ALG", "HS256")],
                    options={"require": ["exp"]},
                    leeway=getattr(settings, "JWT_LEEWAY", 10),
                    audience=getattr(settings, "JWT_AUDIENCE", None),
                    issuer=getattr(settings, "JWT_ISSUER", None),
                )
                request.state.user = payload
            except jwt.ExpiredSignatureError:
                return JSONResponse({"detail": "Token expired"}, status_code=401)
            except jwt.InvalidTokenError:
                return JSONResponse({"detail": "Invalid token"}, status_code=403)

        return await call_next(request)
