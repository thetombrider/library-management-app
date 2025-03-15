from sqlalchemy.orm import Session
from backend.models.book import Book
from backend.models.loan import Loan
from backend.schemas.book import BookCreate, BookUpdate, BookDelete
from fastapi import HTTPException, status
from backend.services.google_books import fetch_book_metadata
from datetime import datetime

def get_books(db: Session, skip: int = 0, limit: int = 10):
    books = db.query(Book).offset(skip).limit(limit).all()
    # Aggiungiamo un flag per indicare se il libro ha una copertina
    for book in books:
        setattr(book, "has_cover", book.cover_image is not None)
    return books

def create_book(db: Session, book: BookCreate):
    # Check per duplicati solo tra i libri dello stesso proprietario
    owner_id = book.owner_id
    
    # Costruisci una query che cerchi libri con lo stesso owner_id
    duplicate_query = db.query(Book).filter(Book.owner_id == owner_id)
    
    # Aggiungi il filtro ISBN o titolo
    if book.isbn:
        duplicate_book = duplicate_query.filter(Book.isbn == book.isbn).first()
    else:
        duplicate_book = duplicate_query.filter(Book.title == book.title).first()
    
    if duplicate_book:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Hai già un libro con lo stesso ISBN o titolo nella tua libreria"
        )
    
    # If ISBN is provided, try to fetch metadata from Google Books API
    if book.isbn:
        metadata = fetch_book_metadata(book.isbn)
        if metadata:
            # Update book data with metadata from Google Books
            book_data = book.model_dump()
            book_data.update(metadata)
            
            # Verifica che l'immagine sia stata recuperata correttamente
            has_cover = metadata.get('cover_image') is not None
            print(f"Cover image retrieved: {has_cover}")
            if has_cover:
                print(f"Cover image size: {len(metadata['cover_image'])} bytes")
            
            db_book = Book(**book_data)
            
            # Verifica dopo la creazione dell'oggetto
            print(f"Book object has cover: {db_book.cover_image is not None}")
        else:
            # If no metadata found, use the provided data
            db_book = Book(**book.model_dump())
    else:
        # No ISBN provided, use the provided data
        db_book = Book(**book.model_dump())
    
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    
    # Imposta il flag has_cover dopo il refresh del database
    setattr(db_book, "has_cover", db_book.cover_image is not None)
    
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
    
    # Verifica se ci sono prestiti attivi per questo libro
    # Un prestito è attivo se non ha data di restituzione o la data è nel futuro
    now = datetime.now()
    active_loans = db.query(Loan).filter(
        Loan.book_id == book_id,
        (Loan.return_date == None) | (Loan.return_date > now)
    ).count()
    
    if active_loans > 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete book with active loans")
    
    # Prima elimina tutti i prestiti (restituiti) associati a questo libro
    db.query(Loan).filter(Loan.book_id == book_id).delete()
    
    # Poi elimina il libro
    db.delete(db_book)
    
    try:
        db.commit()
        return {"message": "Book deleted successfully", "book": db_book}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )