from sqlalchemy.orm import Session
from backend.models.book import Book
from backend.models.loan import Loan
from backend.schemas.book import BookCreate, BookUpdate
from fastapi import HTTPException, status

def get_books(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Book).offset(skip).limit(limit).all()

def create_book(db: Session, book: BookCreate):
    db_book = Book(title=book.title, author=book.author, description=book.description)
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

def update_book(db: Session, book_id: int, book: BookUpdate):
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if not db_book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    for key, value in book.dict().items():
        setattr(db_book, key, value)
    db.commit()
    db.refresh(db_book)
    return db_book

def delete_book(db: Session, book_id: int):
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if not db_book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    
    # Check for any loans associated with the book
    active_loans = db.query(Loan).filter(Loan.book_id == book_id).count()
    if active_loans > 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete book with active loans")
    
    db.delete(db_book)
    db.commit()
    return {"message": "Book deleted successfully", "book": db_book}