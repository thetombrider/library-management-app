from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from backend.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=True)  # Nuovo campo per la password hashata
    role = Column(String, default="user")  # Ruolo: 'admin' o 'user'
    last_login = Column(DateTime, nullable=True)  # Ultimo accesso
    created_at = Column(DateTime, default=lambda: datetime.now(datetime.timezone.utc))  # Data di creazione
    is_active = Column(Boolean, default=True)  # Flag utente attivo

    loans = relationship("Loan", back_populates="user")
    owned_books = relationship("Book", back_populates="owner")