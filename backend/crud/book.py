from sqlalchemy.orm import Session
from backend.models.book import Book
from backend.models.loan import Loan
from backend.schemas.book import BookCreate, BookUpdate, BookDelete
from fastapi import HTTPException, status
from backend.services.google_books import fetch_book_metadata

def get_books(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Book).offset(skip).limit(limit).all()

def create_book(db: Session, book: BookCreate):
    # Check for duplicate books by ISBN if present, otherwise by title
    if book.isbn:
        duplicate_book = db.query(Book).filter(Book.isbn == book.isbn).first()
    else:
        duplicate_book = db.query(Book).filter(Book.title == book.title).first()
    
    if duplicate_book:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Book with the same ISBN or title already exists")
    
    # If ISBN is provided, try to fetch metadata from Google Books API
    if book.isbn:
        metadata = fetch_book_metadata(book.isbn)
        if metadata:
            # Update book data with metadata from Google Books
            book_data = book.dict()
            book_data.update(metadata)
            db_book = Book(**book_data)
        else:
            # If no metadata found, use the provided data
            db_book = Book(**book.model_dump())
    else:
        # No ISBN provided, use the provided data
        db_book = Book(**book.model_dump())
    
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

def update_book(db: Session, book_id: int, book: BookUpdate):
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if not db_book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    for key, value in book.model_dump().items():
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