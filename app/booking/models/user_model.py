# app/booking/models/user.py
from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime
from app.db.base import Base

class User(Base):
    __tablename__ = "user"  # confirma que sea exactamente este nombre; si es "auth_user", cámbialo

    __table_args__ = {
        "extend_existing": True,  # importante si la tabla ya existe
    }

    id = Column(Integer, primary_key=True, index=True)
    password = Column(String(128), nullable=False)
    last_login = Column(DateTime(timezone=True))
    is_superuser = Column(Boolean, nullable=False)
    username = Column(String(150), nullable=False, unique=True)
    first_name = Column(String(150), nullable=False)
    last_name = Column(String(150), nullable=False)
    email = Column(String(254), nullable=False, unique=True)
    is_staff = Column(Boolean, nullable=False)
    is_active = Column(Boolean, nullable=False)
    date_joined = Column(DateTime(timezone=True), nullable=False)
    otp_code = Column(String(10))
    id_card = Column(String(100))
    phone_num = Column(String(20))
    birthdate = Column(Date)
    image = Column(String(100))
    is_available = Column(Boolean, nullable=False)
    dni = Column(String(20))
    is_hide = Column(Boolean, nullable=False)
