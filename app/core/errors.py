from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY, HTTP_500_INTERNAL_SERVER_ERROR

def setup_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_handler(_: Request, exc: RequestValidationError):
        return JSONResponse({"detail": exc.errors()}, status_code=HTTP_422_UNPROCESSABLE_ENTITY)

    @app.exception_handler(IntegrityError)
    async def integrity_handler(_: Request, __: IntegrityError):
        return JSONResponse({"detail": "Integrity error (unique/foreign key)."}, status_code=HTTP_422_UNPROCESSABLE_ENTITY)

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_handler(_: Request, __: SQLAlchemyError):
        return JSONResponse({"detail": "Database error."}, status_code=HTTP_500_INTERNAL_SERVER_ERROR)
