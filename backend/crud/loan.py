from sqlalchemy.orm import Session
from backend.models.loan import Loan
from backend.models.book import Book
from backend.models.user import User
from backend.schemas.loan import LoanCreate, LoanUpdate, LoanDelete
from fastapi import HTTPException, status
from datetime import datetime, timedelta, timezone

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
    db_loan = db.query(Loan).filter(
        Loan.book_id == loan.book_id, 
        Loan.return_date > datetime.now(timezone.utc)
    ).first()
    
    if db_loan:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Book is already loaned out")

    # Set default return date and loan date if not provided
    loan_date = loan.loan_date if loan.loan_date else datetime.now(timezone.utc)
    return_date = loan.return_date if loan.return_date else datetime.now(timezone.utc) + timedelta(days=30)

    db_loan = Loan(book_id=loan.book_id, user_id=loan.user_id, loan_date=loan_date, return_date=return_date)
    db.add(db_loan)
    db.commit()
    db.refresh(db_loan)
    return db_loan

def update_loan(db: Session, loan_id: int, loan: LoanUpdate):
    db_loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not db_loan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")
    
    # Assicuriamo che la data di restituzione includa la timezone UTC
    if loan.return_date and not loan.return_date.tzinfo:
        loan_dict = loan.model_dump()
        loan_dict["return_date"] = loan.return_date.replace(tzinfo=timezone.utc)
        for key, value in loan_dict.items():
            setattr(db_loan, key, value)
    else:
        # Se la data ha già la timezone, usiamo i dati così come sono
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
    return LoanDelete(message="Loan deleted successfully", loan=db_loan)