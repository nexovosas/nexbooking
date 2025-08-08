# inspect_models.py
import os
import sys

# Aseguramos que esté en el contexto correcto
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.db.base import Base
from app.booking.models import image_model, booking_model, accommodation_model, room_model, availability_model, user_model

# Esto asegura que las clases se registren en Base.metadata
def show_registered_tables():
    print("🔍 Tablas registradas en Base.metadata:")
    for table_name in Base.metadata.tables.keys():
        print(f" - {table_name}")

if __name__ == "__main__":
    show_registered_tables()
