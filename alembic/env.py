# alembic/env.py
from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection, create_engine

# =============================================================================
# 1) Resolver rutas del proyecto (funciona aunque llames alembic desde otro cwd)
# =============================================================================
# Estructura esperada:
#   <repo_root>/
#     app/
#     alembic/
#       env.py  ← este archivo
#     alembic.ini
#
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# =============================================================================
# 2) Cargar app + metadata
# =============================================================================
from app.core.config import settings
from app.db.base import Base

# Importa TODOS los modelos para que queden registrados en Base.metadata.
# Soporta tus nombres actuales *_model.py y los “limpios” propuestos.
try:
    # Nombres “limpios” propuestos (si ya migraste archivos)
    from app.booking.models import (
        accommodation as _accommodation,  # noqa: F401
        room as _room,                    # noqa: F401
        booking as _booking,              # noqa: F401
        availability as _availability,    # noqa: F401
        image as _image,                  # noqa: F401
    )
except Exception:
    # Nombres actuales
    from app.booking.models import (
        accommodation_model as _accommodation,  # noqa: F401
        room_model as _room,                    # noqa: F401
        booking_model as _booking,              # noqa: F401
        availability_model as _availability,    # noqa: F401
        image_model as _image,                  # noqa: F401
    )

# Si mapeas la tabla de usuarios de Django para FKs, su import es seguro; la
# excluimos de migraciones con include_object (abajo).
try:
    from app.booking.models import user_model as _user  # noqa: F401
except Exception:
    pass

# =============================================================================
# 3) Config de Alembic
# =============================================================================
config = context.config

# Logging de Alembic (usa alembic.ini)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata objetivo para autogenerate
target_metadata = Base.metadata

# Inyecta la URL en la config (alembic.ini) escapando '%' para evitar la
# interpolación de configparser (p.ej. passwords con %3F, %40, etc.)
if settings.SQLALCHEMY_DATABASE_URI:
    safe_url = str(settings.SQLALCHEMY_DATABASE_URI).replace("%", "%%")
    config.set_main_option("sqlalchemy.url", safe_url)

# =============================================================================
# 4) Política de qué tablas migrar
# =============================================================================
# ✅ LISTA BLANCA (whitelist): SOLO estas tablas gestionará Alembic aquí
BOOKING_TABLES = {
    "accommodations",
    "rooms",
    "bookings",
    "availabilities",
    "images",
}

# ❌ Tablas de Django (y prefijo) a excluir (doble seguro)
DJANGO_TABLES = {
    "user",            # o "auth_user" según tu DB
    "auth_user",
    "auth_group",
    "auth_group_permissions",
    "auth_permission",
    "django_content_type",
    "django_migrations",
    "django_admin_log",
}

def include_object(object, name, type_, reflected, compare_to):
    """
    Control fino sobre qué objetos incluye Alembic en autogenerate.

    Regla:
      - Tablas: incluir SOLO si están en BOOKING_TABLES.
      - Índices/constraints/columnas: incluir solo si su tabla padre está en BOOKING_TABLES.
      - Excluir explícitamente tablas de Django (por nombre o prefijo 'django_').
    """
    # Excluir por nombre exacto (Django)
    if type_ == "table" and (name in DJANGO_TABLES or name.startswith("django_")):
        return False

    # Incluir solo tablas propias del microservicio
    if type_ == "table":
        return name in BOOKING_TABLES

    # Para objetos dependientes (índices, constraints, columnas), revisa tabla padre
    parent_table = getattr(object, "table", None)
    if parent_table is not None:
        return parent_table.name in BOOKING_TABLES

    # Si no sabemos, mejor no incluir
    return False

# =============================================================================
# 5) (Opcional) Filtro anti-DROP en autogenerate
# =============================================================================
# Evita que un autogenerate elimine objetos fuera de BOOKING_TABLES aunque los vea.
# Útil si hay confusión por metadata reflejada o renombres.
from alembic.operations.ops import DropTableOp, DropIndexOp, DropConstraintOp

def process_revision_directives(context, revision, directives):
    # Solo aplica cuando el comando es "revision --autogenerate"
    if not getattr(context.config, "cmd_opts", None):
        return
    if not getattr(context.config.cmd_opts, "autogenerate", False):
        return

    script = directives[0]

    def keep_op(op):
        # Permite drops solo si la tabla está en nuestra whitelist
        if isinstance(op, (DropTableOp, DropIndexOp, DropConstraintOp)):
            tbl = getattr(op, "table_name", None) or getattr(getattr(op, "table", None), "name", None)
            return tbl in BOOKING_TABLES
        return True

    script.upgrade_ops.ops = [op for op in script.upgrade_ops.ops if keep_op(op)]
    if script.downgrade_ops:
        script.downgrade_ops.ops = [op for op in script.downgrade_ops.ops if keep_op(op)]

# =============================================================================
# 6) Modos offline / online
# =============================================================================
def run_migrations_offline() -> None:
    """Ejecuta migraciones sin conexión (genera SQL)."""
    url = str(settings.SQLALCHEMY_DATABASE_URI)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        process_revision_directives=process_revision_directives,
        compare_type=True,               # detecta cambios de tipos
        compare_server_default=True,     # detecta cambios de server_default
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Ejecuta migraciones con conexión real a la DB."""
    connectable = create_engine(str(settings.SQLALCHEMY_DATABASE_URI), poolclass=pool.NullPool)

    # type: Connection
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            process_revision_directives=process_revision_directives,
            compare_type=True,
            compare_server_default=True,
            render_as_batch=False,  # True si alguna vez migras en SQLite
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
