from fastapi import FastAPI
from starlette.middleware import Middleware
from app.middleware.auth_middleware import AuthMiddleware

from app.booking.routes import (
    booking_router,
    accommodation_router,
    rooms_router,
    availability_router
)

middleware = [Middleware(AuthMiddleware)]
app = FastAPI(middleware=middleware)

app.include_router(booking_router, prefix="/booking")
app.include_router(accommodation_router, prefix="/accommodations")
app.include_router(rooms_router, prefix="/rooms")
app.include_router(availability_router, prefix="/availability")
