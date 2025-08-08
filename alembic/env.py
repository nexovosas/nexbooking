# alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys
import os

# Agrega la ruta de la aplicación al sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

# Importa el motor de la base de datos
from app.db.session import SQLALCHEMY_ENGINE
# Importa el objeto 'settings'
from app.core.config import settings
# Importa la clase Base
from app.db.base import Base

# --- Importaciones de modelos: ESTO ES LO CLAVE ---
# Importa todos tus módulos de modelos aquí para que Alembic los detecte.
# No los importes en app/db/base.py.

from app.booking.models import image_model,booking_model, accommodation_model, room_model, availability_model, user_model

# Agrega cualquier otro modelo que tengas aquí.

# Configuración de Alembic
config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata
def include_specific_tables(object, name, type_, reflected, compare_to):
    # Aquí defines exactamente las tablas que deseas que Alembic detecte
    included_tables = {
        "accommodations",
        "rooms",
        "bookings",
        "availabilities",
        "images"
    }

    return type_ == "table" and name in included_tables


def run_migrations_offline():
    context.configure(
        url=settings.SQLALCHEMY_DATABASE_URI,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = SQLALCHEMY_ENGINE

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            include_object=include_specific_tables
        )


        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
