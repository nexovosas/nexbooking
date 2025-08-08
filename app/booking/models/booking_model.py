from sqlalchemy import Column, Integer, Date, ForeignKey,Enum,Float
from sqlalchemy.orm import relationship
from app.db.base import Base
import enum
from sqlalchemy import String, UniqueConstraint

# Definimos un Enum de Python para los posibles estados de la reserva
class BookingStatus(enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"

# Modelo que representa una reserva realizada por un usuario
class Booking(Base):  # Reserva
    __tablename__ = "bookings"  # Nombre de la tabla en la base de datos

    id = Column(Integer, primary_key=True)  # ID único de la reserva
    
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)# ID del usuario que realizó la reserva (relación con tabla users)

    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)# ID de la habitación reservada (relación con tabla rooms)
    
    start_date = Column(Date, nullable=False)# Fecha de inicio de la reserva
    
    end_date = Column(Date, nullable=False)# Fecha de fin de la reserva
    
    guests = Column(Integer)# Número de huéspedes (personas que se hospedarán)
    
    status = Column(Enum(BookingStatus), nullable=False, default=BookingStatus.pending)# Estado de la reserva
    code = Column(String(20), unique=True, nullable=False)  # Código único
    total_price = Column(Float, nullable=False)  # 💰 Total a pagar por la reserva
    user = relationship("User")# Relación con el modelo User para acceder a los datos del usuario
    room = relationship("Room")# Relación con el modelo Room para acceder a los datos de la habitación
