# reset_models.py

from app.db.session import SQLALCHEMY_ENGINE
from app.db.base import Base

# Importa solo los modelos que quieres incluir (excluyendo user_model)
from app.booking.models import (
    image_model,
    booking_model,
    accommodation_model,
    room_model,
    availability_model
)

# Lista explícita de tablas a resetear
INCLUDED_TABLES = {
    "accommodations",
    "rooms",
    "bookings",
    "availabilities",
    "images"
}

# Filtra las tablas del metadata según la lista
tables_to_reset = [
    table for table in Base.metadata.sorted_tables
    if table.name in INCLUDED_TABLES
]

# 1. Borrar las tablas seleccionadas
print("🚨 Borrando tablas:")
for table in tables_to_reset:
    print(f" - {table.name}")
Base.metadata.drop_all(bind=SQLALCHEMY_ENGINE, tables=tables_to_reset)

print("\n🎉 ¡Listo! Solo esas tablas fueron reiniciadas correctamente.")
