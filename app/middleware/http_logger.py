# app/middleware/http_logger.py
import os
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("app.http")

LOG_BODY = os.getenv("LOG_BODY", "false").lower() == "true"
MAX_BODY = int(os.getenv("LOG_BODY_MAX", "2048"))  # bytes máx. a loggear


def _safe_trunc(b: bytes | str, n: int) -> str:
    try:
        if isinstance(b, bytes):
            b = b.decode(errors="replace")
        return b[:n]
    except Exception:
        return "<unreadable>"


class HTTPLoggerMiddleware(BaseHTTPMiddleware):
    """
    Log de acceso: método, path, status, latencia, ip, origin, ua, size, rid, user_id (si disponible).
    Evita loggear cuerpos salvo que LOG_BODY=true (y trunca a LOG_BODY_MAX).
    """

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()

        # Datos de request
        path = request.url.path
        method = request.method
        client_ip = request.headers.get("x-forwarded-for") or (request.client.host if request.client else "-")
        origin = request.headers.get("origin")
        ua = request.headers.get("user-agent", "-")
        host = request.headers.get("host", "-")
        rid = getattr(request.state, "request_id", "-")

        body_snippet = None
        if LOG_BODY and method in ("POST", "PUT", "PATCH"):
            try:
                body = await request.body()
                body_snippet = _safe_trunc(body, MAX_BODY)
                # Reinyecta el body para no consumir el stream
                request = Request(request.scope, receive=lambda: {"type": "http.request", "body": body, "more_body": False})
            except Exception:
                body_snippet = "<error-reading-body>"

        try:
            response = await call_next(request)
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            logger.exception(f"request_failed method={method} path={path} host={host} ip={client_ip} rid={rid} in_ms={elapsed:.2f}")
            raise e

        elapsed = (time.perf_counter() - start) * 1000
        status = response.status_code
        size = response.headers.get("content-length") or "-"

        # Intenta capturar user_id si tu AuthMiddleware lo coloca en state
        user_id = getattr(request.state, "user_id", None) or "-"

        # Mensaje compacto clave=valor (fácil de parsear por Loki/ELK)
        msg = (
            f"access method={method} path={path} status={status} in_ms={elapsed:.2f} "
            f"ip={client_ip} host={host} origin={origin} ua=\"{ua}\" size={size} rid={rid} user_id={user_id}"
        )
        if body_snippet is not None:
            msg += f" body=\"{body_snippet}\""

        if status >= 500:
            logger.error(msg)
        elif status >= 400:
            logger.warning(msg)
        else:
            logger.info(msg)

        return response
