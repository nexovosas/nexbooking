from fastapi import FastAPI
from starlette.middleware import Middleware
from starlette.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.errors import setup_exception_handlers

from fastapi.openapi.utils import get_openapi
from app.middleware.auth_middleware import AuthMiddleware
from app.booking.routes import (
    booking_router,
    accommodation_router,
    rooms_router,
    availability_router,
)

API_PREFIX = "/api/v1"

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: Cambiar en producción por dominios permitidos
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    ),
    Middleware(GZipMiddleware),
    Middleware(
        AuthMiddleware,
        exempt_paths={
            "/",
            f"{API_PREFIX}/health",
            f"{API_PREFIX}/docs",
            f"{API_PREFIX}/openapi.json",
        },
    ),
]

app = FastAPI(
    title="Nexovo Booking API",
    version="0.1.0",
    summary="Booking microservice for accommodations, rooms, and availability.",
    description=(
        "This service manages accommodations, rooms, and availability, including search, "
        "pricing, and host-owned resources."
    ),
    docs_url=f"{API_PREFIX}/docs",
    redoc_url=f"{API_PREFIX}/redoc",
    openapi_url=f"{API_PREFIX}/openapi.json",
    middleware=middleware,
    contact={
        "name": "Nexovo Dev Team",
        "email": "support@nexovo.com",
        "url": "https://nexovo.com.co/developers",
    },
    license_info={
        "name": "Proprietary License",
        "url": "https://nexovo.com.co/license",
    },
    servers=[
        {"url": API_PREFIX, "description": "Current base path"},
    ],
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Branding (aparece en Redoc)
    openapi_schema["info"]["x-logo"] = {
        "url": "https://nexovo.com.co/light_logo.png",
        "altText": "Nexovo",
        "backgroundColor": "#0A122A",
    }

    # Servers visibles en Swagger/Redoc (además del que pusiste en FastAPI)
    openapi_schema["servers"] = [
        {"url": "https://api.nexovo.com.co", "description": "Production"},
        {"url": "http://127.0.0.1:5000", "description": "Local"},
        {"url": API_PREFIX, "description": "Mounted base path"},
    ]

    # Seguridad global: Bearer JWT
    comps = openapi_schema.setdefault("components", {})
    sec = comps.setdefault("securitySchemes", {})
    sec.update({
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    })
    openapi_schema["security"] = [{"BearerAuth": []}]

    # Descripciones de tags (opcional, si usas estos tags)
    openapi_schema["tags"] = [
        {"name": "Accommodations", "description": "Create, search, update, and delete accommodations."},
        {"name": "Rooms", "description": "Room inventory and pricing."},
        {"name": "Availability", "description": "Calendar availability management."},
    ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi


setup_exception_handlers(app)

@app.get("/")
def root():
    return {"ok": True, "service": "booking"}

@app.get(f"{API_PREFIX}/health")
def health():
    return {"status": "healthy"}

# Routers
# app.include_router(booking_router, prefix=f"{API_PREFIX}/booking", tags=["Booking"])
# app.include_router(accommodation_router, prefix=f"{API_PREFIX}/accommodations", tags=["Accommodations"])
# app.include_router(rooms_router, prefix=f"{API_PREFIX}/rooms", tags=["Rooms"])
# app.include_router(availability_router, prefix=f"{API_PREFIX}/availability", tags=["Availability"])

# Opción A: cada router define su propio prefix interno
app.include_router(booking_router,       prefix=API_PREFIX, tags=["Bookings"])
app.include_router(accommodation_router, prefix=API_PREFIX, tags=["Accommodations"])
app.include_router(rooms_router,         prefix=API_PREFIX, tags=["Rooms"])
app.include_router(availability_router,  prefix=API_PREFIX, tags=["Availability"])
