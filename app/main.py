# app/main.py
from fastapi import FastAPI
from starlette.middleware import Middleware
from starlette.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware

from app.middleware.auth_middleware import AuthMiddleware
from app.booking.routes import (
    booking_router,
    accommodation_router,
    rooms_router,
    availability_router,
)

# Prefijo base de la API (recomendado para microservicios)
API_PREFIX = "/api/v1"

# Lista de middlewares
middleware = [
    # CORS primero para que las peticiones OPTIONS no sean bloqueadas por la autenticación
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],  # En producción poner solo dominios permitidos
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    ),
    Middleware(GZipMiddleware),  # Compresión de respuestas
    Middleware(
        AuthMiddleware,
        exempt_paths={  # Rutas que no requieren autenticación
            "/",
            f"{API_PREFIX}/health",
            f"{API_PREFIX}/docs",
            f"{API_PREFIX}/openapi.json",
        },
    ),
]

# Inicializar aplicación
app = FastAPI(
    title="Nexovo Booking API",
    version="0.1.0",
    docs_url=f"{API_PREFIX}/docs",
    openapi_url=f"{API_PREFIX}/openapi.json",
    middleware=middleware,
)

# Ruta raíz y de salud
@app.get("/")
def root():
    return {"ok": True, "service": "booking"}

@app.get(f"{API_PREFIX}/health")
def health():
    return {"status": "healthy"}

# Incluir routers
app.include_router(booking_router, prefix=f"{API_PREFIX}/booking", tags=["Booking"])
app.include_router(accommodation_router, prefix=f"{API_PREFIX}/accommodations", tags=["Accommodations"])
app.include_router(rooms_router, prefix=f"{API_PREFIX}/rooms", tags=["Rooms"])
app.include_router(availability_router, prefix=f"{API_PREFIX}/availability", tags=["Availability"])
