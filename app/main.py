from fastapi import FastAPI, Request, Depends
from starlette.middleware import Middleware
from starlette.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.core.config import settings
from app.core.errors import setup_exception_handlers
from app.auth.verify_token import verify_token
from app.booking.uploads.routes import router as uploads_router
from app.booking.routes import (
    booking_router,
    accommodation_router,
    rooms_router,
    availability_router,
)

API_PREFIX = "/api/v1"

# -----------------------------------------------------------------------------
# Middleware (sin AuthMiddleware)
# -----------------------------------------------------------------------------
middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=[
            "https://nexovo.com.co",
            "http://localhost",
            "http://127.0.0.1",
            "http://localhost:3000",
            "http://localhost:5000",
            "http://localhost:5173",
        ],
        allow_origin_regex=r"^https:\/\/(?:[a-z0-9-]+\.)*nexovo\.com\.co$",
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["Authorization", "Content-Type", "*"],
        expose_headers=["*"],
    ),
    Middleware(GZipMiddleware),
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

    openapi_schema["info"]["x-logo"] = {
        "url": "https://nexovo.com.co/light_logo.png",
        "altText": "Nexovo",
        "backgroundColor": "#0A122A",
    }

    openapi_schema["servers"] = [
        {"url": "https://booking.nexovo.com.co", "description": "Production"},
        {"url": "http://127.0.0.1:5000", "description": "Local"},
        {"url": "/", "description": "Mounted base path"},
    ]

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

@app.get(f"{API_PREFIX}/_debug/cookies", tags=["Debug"])
def debug_cookies(req: Request):
    return {
        "cookies": dict(req.cookies),
        "auth_header": req.headers.get("authorization"),
    }

@app.get(f"{API_PREFIX}/_debug/me", tags=["Debug"])
def debug_me(user = Depends(verify_token)):
    return {"claims": user}

# -----------------------------------------------------------------------------
# Routers
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
