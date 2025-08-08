# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Usa tu URL de PostgreSQL aquí para que la aplicación se conecte a la base de datos correcta.
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:c3qxmc7n4kojjila@31.97.12.66:5432/nexovo"

# Crear el engine. No necesitas connect_args si usas PostgreSQL.
engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()