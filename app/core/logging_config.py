# app/core/logging.py
import logging, sys, json, uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from time import perf_counter

def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(message)s')  # emitiremos JSON
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers = [handler]

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start = perf_counter()
        response = None
        try:
            response = await call_next(request)
            return response
        finally:
            took = (perf_counter() - start) * 1000
            log = {
                "ts": request.state.__dict__.get("ts"),
                "level": "INFO",
                "request_id": req_id,
                "method": request.method,
                "path": request.url.path,
                "status": getattr(response, "status_code", 500),
                "ms": round(took, 2),
                "client": request.client.host if request.client else None,
            }
            logging.getLogger("app").info(json.dumps(log))
