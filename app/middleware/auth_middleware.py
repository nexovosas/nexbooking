# app/middleware/auth_middleware.py
from typing import Callable, Iterable
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.responses import JSONResponse
import jwt
from app.core.config import settings

EXEMPT_PATHS = {
    "/", 
    f"{settings.API_PREFIX}/health",
    f"{settings.API_PREFIX}/docs",
    f"{settings.API_PREFIX}/openapi.json",
}
PROTECTED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

class AuthMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        path: str = scope.get("path", "")
        method: str = scope.get("method", "GET")

        # Rutas públicas y preflight
        if path in EXEMPT_PATHS or method == "OPTIONS":
            return await self.app(scope, receive, send)

        if method in PROTECTED_METHODS:
            headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
            auth_header = headers.get("authorization", "").strip()

            if not auth_header.lower().startswith("bearer "):
                return await JSONResponse({"detail": "Authorization token required"}, status_code=401)(scope, receive, send)

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
                # adjuntar user al scope (compatible con request.state en FastAPI)
                scope.setdefault("state", {})["user"] = payload
            except jwt.ExpiredSignatureError:
                return await JSONResponse({"detail": "Token expired"}, status_code=401)(scope, receive, send)
            except jwt.InvalidTokenError:
                return await JSONResponse({"detail": "Invalid token"}, status_code=403)(scope, receive, send)

        return await self.app(scope, receive, send)
