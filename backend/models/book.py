from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author = Column(String, index=True)
    description = Column(String, index=True)
    isbn = Column(String, index=True, nullable=True)
    publisher = Column(String, nullable=True)
    publish_year = Column(Integer, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    loans = relationship("Loan", back_populates="book")
    owner = relationship("User", back_populates="owned_books")