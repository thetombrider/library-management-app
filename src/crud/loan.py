from sqlalchemy.orm import Session
from src.models.loan import Loan
from src.models.book import Book
from src.models.user import User
from src.schemas.loan import LoanCreate, LoanUpdate
from fastapi import HTTPException, status
from datetime import datetime

def get_loans(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Loan).offset(skip).limit(limit).all()

def create_loan(db: Session, loan: LoanCreate):
    # Check if the book exists
    db_book = db.query(Book).filter(Book.id == loan.book_id).first()
    if not db_book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    # Check if the user exists
    db_user = db.query(User).filter(User.id == loan.user_id).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Check if the book is already loaned out
    db_loan = db.query(Loan).filter(Loan.book_id == loan.book_id, (Loan.return_date == None) | (Loan.return_date > datetime.utcnow())).first()
    if db_loan:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Book is already loaned out")

    db_loan = Loan(**loan.model_dump())
    db.add(db_loan)
    db.commit()
    db.refresh(db_loan)
    return db_loan

def update_loan(db: Session, loan_id: int, loan: LoanUpdate):
    db_loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not db_loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")
    for key, value in loan.model_dump().items():
        setattr(db_loan, key, value)
    db.commit()
    db.refresh(db_loan)
    return db_loan

def delete_loan(db: Session, loan_id: int):
    db_loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not db_loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")
    db.delete(db_loan)
    db.commit()
    return {"message": "Loan deleted successfully", "loan": db_loan}