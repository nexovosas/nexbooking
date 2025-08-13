# app/core/errors.py

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from starlette.status import (
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_409_CONFLICT,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

PROBLEM_JSON = "application/problem+json"


def _jsonable_validation_errors(errs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Convierte cualquier campo no serializable en str (e.g. UploadFile en 'input' o
    tipos raros en 'ctx'), evitando TypeError al json.dumps().
    """
    cleaned: list[dict[str, Any]] = []
    for e in errs:
        item = dict(e)
        # Normaliza 'input'
        if "input" in item:
            try:
                json.dumps(item["input"])
            except TypeError:
                item["input"] = str(item["input"])

        # Normaliza 'ctx'
        ctx = item.get("ctx")
        if isinstance(ctx, dict):
            for k, v in list(ctx.items()):
                try:
                    json.dumps(v)
                except TypeError:
                    ctx[k] = str(v)
            item["ctx"] = ctx

        cleaned.append(item)
    return cleaned


def _pg_error_info(exc: IntegrityError) -> tuple[str | None, str | None]:
    """
    Extrae pgcode y constraint si vienen de psycopg. Devuelve (pgcode, constraint_name).
    """
    orig = getattr(exc, "orig", None)
    pgcode = getattr(orig, "pgcode", None)
    diag = getattr(orig, "diag", None)
    constraint = getattr(diag, "constraint_name", None)
    return pgcode, constraint


def setup_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        error_id = str(uuid.uuid4())
        cleaned = _jsonable_validation_errors(exc.errors())

        logging.info(
            "422 ValidationError %s %s err_id=%s errors=%s",
            request.method,
            request.url.path,
            error_id,
            cleaned,
        )

        payload = {
            "type": "https://errors.nexovo.com/validation-error",
            "title": "Validation error",
            "status": HTTP_422_UNPROCESSABLE_ENTITY,
            "detail": "Request validation failed.",
            "instance": str(request.url),
            "errors": cleaned,
            "error_id": error_id,
        }
        return JSONResponse(
            payload,
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            media_type=PROBLEM_JSON,
        )

    @app.exception_handler(IntegrityError)
    async def integrity_handler(request: Request, exc: IntegrityError):
        error_id = str(uuid.uuid4())
        pgcode, constraint = _pg_error_info(exc)

        # Valores por defecto
        status = HTTP_422_UNPROCESSABLE_ENTITY
        title = "Integrity error"
        detail = "Integrity constraint violated."

        # Ajustes por código Postgres
        # 23505 unique_violation → 409 Conflict
        # 23503 foreign_key_violation → 422
        # 23502 not_null_violation → 422
        # 23514 check_violation → 422
        if pgcode == "23505":
            status = HTTP_409_CONFLICT
            title = "Unique constraint violation"
            detail = "A record with the same unique value already exists."
        elif pgcode == "23503":
            title = "Foreign key violation"
            detail = "Referenced record not found or FK constraint failed."
        elif pgcode == "23502":
            title = "Not-null violation"
            detail = "A required column received a NULL value."
        elif pgcode == "23514":
            title = "Check constraint violation"
            detail = "A check constraint failed."

        logging.warning(
            "DB IntegrityError code=%s constraint=%s path=%s err_id=%s",
            pgcode,
            constraint,
            request.url.path,
            error_id,
            exc_info=True,  # registra stacktrace
        )

        payload = {
            "type": f"https://errors.nexovo.com/db/{pgcode or 'integrity'}",
            "title": title,
            "status": status,
            "detail": detail,
            "instance": str(request.url),
            "error_id": error_id,
            "extras": {"pgcode": pgcode, "constraint": constraint},
        }
        return JSONResponse(payload, status_code=status, media_type=PROBLEM_JSON)

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_handler(request: Request, exc: SQLAlchemyError):
        error_id = str(uuid.uuid4())

        # Log completo con stacktrace
        logging.exception(
            "SQLAlchemyError on %s %s err_id=%s",
            request.method,
            request.url.path,
            error_id,
        )

        payload = {
            "type": "https://errors.nexovo.com/db/error",
            "title": "Database error",
            "status": HTTP_500_INTERNAL_SERVER_ERROR,
            "detail": "An unexpected database error occurred.",
            "instance": str(request.url),
            "error_id": error_id,
        }
        return JSONResponse(
            payload,
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            media_type=PROBLEM_JSON,
        )
