from functools import lru_cache
from urllib.parse import quote_plus
from pydantic import Field, EmailStr, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # === Opción 1: URL completa (si la defines, se usa tal cual) ===
    DATABASE_URL: str | None = None  # ej: postgresql+psycopg://user:pass@host:5432/dbname

    # === Opción 2: Partes sueltas (se usan si DATABASE_URL es None) ===
    POSTGRES_DRIVER: str = Field(default="postgresql+psycopg")  # o "postgresql"
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432, ge=1, le=65535)
    POSTGRES_DB: str = Field(default="postgres")
    POSTGRES_USER: str = Field(default="postgres")
    POSTGRES_PASSWORD: str = Field(default="postgres")

    # === Seguridad / JWT ===
    SECRET_KEY: str = Field(..., min_length=32)
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_EXPIRE_MINUTES: int = Field(default=60 * 24)

    # === Email / SMTP ===
    EMAIL_USE_SSL: bool = True
    EMAIL_HOST: str = Field(default="smtp.hostinger.com")
    EMAIL_HOST_USER: EmailStr | None = None
    EMAIL_HOST_PASSWORD: str | None = None
    EMAIL_PORT: int = 465
    SMTP_FROM: EmailStr | None = None
    SMTP_REPLY_TO: EmailStr | None = None

    # === Derivado ===
    SQLALCHEMY_DATABASE_URI: PostgresDsn | str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("POSTGRES_DB", mode="before")
    @classmethod
    def strip_leading_slash_from_db(cls, v: str) -> str:
        # Evita “//dbname” al construir la URI
        return v.lstrip("/") if isinstance(v, str) else v

    def __init__(self, **data):
        super().__init__(**data)

        if self.DATABASE_URL:
            # Valida formato básico (deja pasar sin tocar si es correcto)
            self.SQLALCHEMY_DATABASE_URI = self.DATABASE_URL
            return

        # Construcción segura con partes
        user = quote_plus(self.POSTGRES_USER)
        pwd = quote_plus(self.POSTGRES_PASSWORD)
        host = self.POSTGRES_HOST
        port = int(self.POSTGRES_PORT)
        db = self.POSTGRES_DB

        # f-string robusta (evita problemas del builder con tipos/“/”)
        self.SQLALCHEMY_DATABASE_URI = (
            f"{self.POSTGRES_DRIVER}://{user}:{pwd}@{host}:{port}/{db}"
        )


@lru_cache
def get_settings() -> "Settings":
    return Settings()


settings = get_settings()
