# app/middleware/auth_middleware.py
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException
import jwt
from app.core.config import settings  # importa settings


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Solo proteger métodos que modifican datos
        protected_methods = {"POST", "PUT", "DELETE"}

        if request.method in protected_methods:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(status_code=403, detail="Authorization token required")

            token = auth_header.split(" ")[1]
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
                request.state.user = payload
            except jwt.PyJWTError:
                raise HTTPException(status_code=403, detail="Invalid token")

        return await call_next(request)
