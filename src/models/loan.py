from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from src.database import Base

class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    loan_date = Column(DateTime, nullable=False)
    return_date = Column(DateTime, nullable=True)

    book = relationship("Book", back_populates="loans")
    user = relationship("User", back_populates="loans")