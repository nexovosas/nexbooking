# alembic/env.py
from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool, create_engine, Table, Column, Integer
from sqlalchemy.engine import Connection

# =============================================================================
# 1) Resolver rutas del proyecto
# =============================================================================
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# =============================================================================
# 2) Cargar app + metadata
# =============================================================================
from app.core.config import settings
from app.db.base import Base

# --- IMPORTA TODOS LOS MODELOS DEL MÓDULO BOOKING (para poblar Base.metadata) ---
# Soporta variantes *_model.py y nombres “limpios”
try:
    from app.booking.models import (
        accommodation as _accommodation,  # noqa: F401
        room as _room,                    # noqa: F401
        booking as _booking,              # noqa: F401
        availability as _availability,    # noqa: F401
        image as _image,                  # noqa: F401
    )
except Exception:
    from app.booking.models import (
        accommodation_model as _accommodation,  # noqa: F401
        room_model as _room,                    # noqa: F401
        booking_model as _booking,              # noqa: F401
        availability_model as _availability,    # noqa: F401
        image_model as _image,                  # noqa: F401
    )

# Intenta registrar también la tabla de usuarios (para resolver FKs)
def ensure_user_table_in_metadata() -> None:
    """
    Asegura que 'user' exista en Base.metadata (solo para resolver FKs).
    Si no se puede importar el modelo, inyecta una tabla mínima user(id)
    marcada con skip_autogenerate para que Alembic NO la migre.
    """
    if "user" in Base.metadata.tables:
        return
    try:
        # Intento 1: importar tu modelo real
        import app.booking.models.user_model as _user  # noqa: F401
        # Si el import registra la tabla en Base.metadata, listo
        if "user" in Base.metadata.tables:
            return
    except Exception:
        pass
    # Intento 2 (fallback): inyectar tabla mínima
    Table(
        "user",
        Base.metadata,
        Column("id", Integer, primary_key=True),
        schema="public",
        info={"skip_autogenerate": True},
        keep_existing=True,
    )

ensure_user_table_in_metadata()

# =============================================================================
# 3) Config de Alembic
# =============================================================================
config = context.config

# Logging de Alembic (usa alembic.ini)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata objetivo para autogenerate (tras importar/inyectar todo)
target_metadata = Base.metadata

# Inyecta la URL en la config escapando '%'
if settings.SQLALCHEMY_DATABASE_URI:
    safe_url = str(settings.SQLALCHEMY_DATABASE_URI).replace("%", "%%")
    config.set_main_option("sqlalchemy.url", safe_url)

# =============================================================================
# 4) Política de qué tablas migrar
# =============================================================================
BOOKING_TABLES = {
    "accommodations",
    "rooms",
    "bookings",
    "availabilities",  # verifica que __tablename__ sea exactamente este
    "images",
}

DJANGO_TABLES = {
    "user",            # Django en tu caso
    "auth_user",
    "auth_group",
    "auth_group_permissions",
    "auth_permission",
    "django_content_type",
    "django_migrations",
    "django_admin_log",
}

def include_object(obj, name, type_, reflected, compare_to):
    """
    Regla:
      - Tablas: incluir SOLO si están en BOOKING_TABLES, y excluir explícitamente las de Django.
      - Objetos dependientes (índices/constraints/columnas): incluir solo si su tabla padre está en BOOKING_TABLES.
      - Además, ignora cualquier tabla marcada con info.skip_autogenerate.
    """
    # Ignorar tablas marcadas para saltar
    if type_ == "table" and getattr(obj, "info", {}).get("skip_autogenerate", False):
        return False

    # Excluir por nombre exacto (Django) o prefijo
    if type_ == "table" and (name in DJANGO_TABLES or name.startswith("django_")):
        return False

    # Incluir solo tablas propias del microservicio
    if type_ == "table":
        return name in BOOKING_TABLES

    # Para objetos dependientes, revisa tabla padre
    parent_table = getattr(obj, "table", None)
    if parent_table is not None:
        return parent_table.name in BOOKING_TABLES

    return False

# =============================================================================
# 5) (Opcional) Filtro anti-DROP en autogenerate
# =============================================================================
from alembic.operations.ops import DropTableOp, DropIndexOp, DropConstraintOp

def process_revision_directives(context, revision, directives):
    if not getattr(context.config, "cmd_opts", None):
        return
    if not getattr(context.config.cmd_opts, "autogenerate", False):
        return

    script = directives[0]

    def keep_op(op):
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
    url = str(settings.SQLALCHEMY_DATABASE_URI)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        process_revision_directives=process_revision_directives,
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = create_engine(str(settings.SQLALCHEMY_DATABASE_URI), poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            process_revision_directives=process_revision_directives,
            compare_type=True,
            compare_server_default=True,
            include_schemas=True,
            render_as_batch=False,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
