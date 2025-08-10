# app/middleware/request_id.py
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import contextvars

# Contextvar global para inyectar en logs
request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    - Lee X-Request-ID si viene del proxy/cliente; si no, genera uno.
    - Lo propaga en request.state, contextvar y response header.
    """

    def __init__(self, app, header_name: str = "X-Request-ID"):
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get(self.header_name)
        if not rid:
            rid = str(uuid.uuid4())
        request.state.request_id = rid
        token = request_id_var.set(rid)

        try:
            response: Response = await call_next(request)
        finally:
            # Limpia el contextvar para no filtrar a otras peticiones
            request_id_var.reset(token)

        response.headers[self.header_name] = rid
        return response
