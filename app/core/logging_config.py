import logging
import os
from logging.config import dictConfig

# Contexto opcional (request id)
try:
    from app.middleware.request_id import request_id_var  # contextvar
except Exception:
    request_id_var = None


class HealthFilter(logging.Filter):
    """Evita loggear rutas ruidosas como /health, /docs, /openapi.json, /favicon.ico, raíz."""
    NOISE_PREFIXES = (
        "/api/v1/health",
        "/api/v1/docs",
        "/api/v1/redoc",
        "/api/v1/openapi.json",
        "/favicon.ico",
        "/",
    )

    def filter(self, record: logging.LogRecord) -> bool:
        msg = getattr(record, "msg", "")
        if isinstance(msg, str) and " path=" in msg:
            for p in self.NOISE_PREFIXES:
                if f" path={p}" in msg or f" path=\"{p}\"" in msg:
                    return False
        return True


class RequestIdFilter(logging.Filter):
    """Inyecta request_id desde contextvars en cada registro."""
    def filter(self, record: logging.LogRecord) -> bool:
        req_id = None
        try:
            if request_id_var is not None:
                req_id = request_id_var.get()
        except Exception:
            pass
        record.request_id = req_id or "-"
        return True


def setup_logging():
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_format = os.getenv("LOG_FORMAT", "plain").lower()  # "plain" | "json"

    # ¿Tenemos python-json-logger disponible?
    has_json = False
    if log_format == "json":
        try:
            import pythonjsonlogger  # noqa: F401
            has_json = True
        except Exception:
            has_json = False

    formatters = {
        "plain": {
            "format": "%(levelname)s %(asctime)s [%(name)s] [rid=%(request_id)s] | %(message)s",
        }
    }
    if has_json:
        formatters["json"] = {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "fmt": "%(levelname)s %(asctime)s %(name)s %(request_id)s %(message)s",
        }

    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json" if has_json else "plain",
            "filters": ["request_id", "noise_filter"],
        }
    }

    dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "request_id": {"()": RequestIdFilter},
            "noise_filter": {"()": HealthFilter},
        },
        "formatters": formatters,
        "handlers": handlers,
        "loggers": {
            "uvicorn": {"handlers": ["console"], "level": log_level, "propagate": False},
            "uvicorn.error": {"handlers": ["console"], "level": log_level, "propagate": False},
            "uvicorn.access": {"handlers": ["console"], "level": log_level, "propagate": False},
            "fastapi": {"handlers": ["console"], "level": log_level, "propagate": False},

            "app": {"handlers": ["console"], "level": log_level, "propagate": False},
            "app.http": {"handlers": ["console"], "level": log_level, "propagate": False},
            "app.errors": {"handlers": ["console"], "level": log_level, "propagate": False},
        },
        "root": {"handlers": ["console"], "level": log_level},
    })

    logging.getLogger("app").info(
        f"Logging configured: level={log_level}, format={'json' if has_json else 'plain'}"
    )
