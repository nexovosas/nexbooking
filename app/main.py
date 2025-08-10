from fastapi import FastAPI
from starlette.middleware import Middleware
from starlette.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.core.config import settings
from app.core.errors import setup_exception_handlers
from app.middleware.auth_middleware import AuthMiddleware

from app.booking.uploads.routes import router as uploads_router
from app.booking.routes import (
    booking_router,
    accommodation_router,
    rooms_router,
    availability_router,
)

API_PREFIX = "/api/v1"

# -----------------------------------------------------------------------------
# Middleware
# -----------------------------------------------------------------------------
middleware = [
    Middleware(
        CORSMiddleware,
        # Orígenes útiles en desarrollo local
        allow_origins=[
            "http://localhost",
            "http://127.0.0.1",
            "http://localhost:3000",
            "http://localhost:5000",
            "http://localhost:5173",
        ],
        # Permite https://nexovo.com.co y cualquier subdominio anidado
        allow_origin_regex=r"^https:\/\/(?:[a-z0-9-]+\.)*nexovo\.com\.co$",
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["Authorization", "Content-Type", "*"],
        expose_headers=["*"],
    ),
    Middleware(GZipMiddleware),
    Middleware(
        AuthMiddleware,
        exempt_paths={
            "/",
            f"{API_PREFIX}/health",
            f"{API_PREFIX}/docs",
            f"{API_PREFIX}/redoc",
            f"{API_PREFIX}/openapi.json",
        },
    ),
]

# -----------------------------------------------------------------------------
# App
# -----------------------------------------------------------------------------
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
    # Importante: NO pongas /api/v1 aquí para evitar duplicar en Swagger
    servers=[{"url": "/", "description": "Mounted base path"}],
    redirect_slashes=True,
)

# -----------------------------------------------------------------------------
# OpenAPI con branding y servers correctos
# -----------------------------------------------------------------------------
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Branding (Redoc)
    openapi_schema["info"]["x-logo"] = {
        "url": "https://nexovo.com.co/light_logo.png",
        "altText": "Nexovo",
        "backgroundColor": "#0A122A",
    }

    # Servers visibles en Swagger/Redoc SIN /api/v1 (lo añade el prefix del router)
    openapi_schema["servers"] = [
        {"url": "https://api.nexovo.com.co", "description": "Production"},
        {"url": "http://127.0.0.1:5000", "description": "Local"},
        {"url": "/", "description": "Mounted base path"},
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

    # Descripciones de tags
    openapi_schema["tags"] = [
        {"name": "Accommodations", "description": "Create, search, update, and delete accommodations."},
        {"name": "Rooms", "description": "Room inventory and pricing."},
        {"name": "Availability", "description": "Calendar availability management."},
        {"name": "Bookings", "description": "Booking operations and flows."},
        {"name": "Uploads", "description": "File uploads for booking module."},
    ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# -----------------------------------------------------------------------------
# Health & Root
# -----------------------------------------------------------------------------
@app.get("/")
def root():
    return {"ok": True, "service": "booking"}

@app.get(f"{API_PREFIX}/health")
def health():
    return {"status": "healthy"}

# -----------------------------------------------------------------------------
# Routers (cada router define paths SIN /api/v1 internamente)
# -----------------------------------------------------------------------------
app.include_router(booking_router,       prefix=API_PREFIX, tags=["Bookings"])
app.include_router(accommodation_router, prefix=API_PREFIX, tags=["Accommodations"])
app.include_router(rooms_router,         prefix=API_PREFIX, tags=["Rooms"])
app.include_router(availability_router,  prefix=API_PREFIX, tags=["Availability"])
app.include_router(uploads_router,       prefix=API_PREFIX, tags=["Uploads"])

# -----------------------------------------------------------------------------
# Global exception handlers
# -----------------------------------------------------------------------------
setup_exception_handlers(app)
