from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from backend import crud, models, schemas
from backend.database import get_db
from sqlalchemy import or_
from typing import List
from datetime import datetime

router = APIRouter()

@router.get("/", response_model=list[schemas.Book])
def read_books(
    skip: int = 0, 
    limit: int = 100, 
    current_user: models.User = Depends(crud.user.get_current_user), 
    db: Session = Depends(get_db)
):
    """
    Ottiene la lista dei libri visibili all'utente autenticato:
    - Libri di proprietà dell'utente
    - Libri presi in prestito dall'utente
    """
    # Query per recuperare i libri che appartengono all'utente o che ha in prestito
    user_id = current_user.id
    
    # Debug
    print(f"Fetching books for user ID: {user_id}")
    
    # 1. Libri di proprietà dell'utente (query esplicita)
    owned_books = db.query(models.Book).filter(models.Book.owner_id == user_id).all()
    print(f"Found {len(owned_books)} owned books")
    
    # 2. Libri presi in prestito (prestiti attivi) con query più robusta
    now = datetime.now()
    active_loans = db.query(models.Loan).filter(
        models.Loan.user_id == user_id,
        or_(
            models.Loan.return_date.is_(None),  # Prestiti senza data di restituzione
            models.Loan.return_date > now     # Prestiti con data futura
        )
    ).all()
    
    print(f"Found {len(active_loans)} active loans")
    
    # Recupera gli ID dei libri presi in prestito
    borrowed_book_ids = [loan.book_id for loan in active_loans]
    
    # Recupera i libri corrispondenti (solo se ci sono prestiti)
    borrowed_books = []
    if borrowed_book_ids:
        borrowed_books = db.query(models.Book).filter(models.Book.id.in_(borrowed_book_ids)).all()
    
    print(f"Found {len(borrowed_books)} borrowed books")
    
    # Unisci i due set di libri (proprietà + prestiti)
    # Usiamo un dizionario per evitare duplicati
    all_visible_books_dict = {book.id: book for book in owned_books}
    for book in borrowed_books:
        if book.id not in all_visible_books_dict:
            all_visible_books_dict[book.id] = book
    
    all_visible_books = list(all_visible_books_dict.values())
    print(f"Total visible books: {len(all_visible_books)}")
    
    # Imposta il flag has_cover per ciascun libro
    for book in all_visible_books:
        setattr(book, "has_cover", book.cover_image is not None)
    
    # Implementa paginazione
    start = skip
    end = skip + limit if limit and skip + limit < len(all_visible_books) else len(all_visible_books)
    return all_visible_books[start:end]

@router.post("/", response_model=schemas.Book)
def create_book(book: schemas.BookCreate, current_user: models.User = Depends(crud.user.get_current_user), db: Session = Depends(get_db)):
    # Prima dell'implementazione attuale, assegna l'owner_id
    # se non è già specificato e l'utente è autenticato
    book_data = book.model_dump()
    
    # Imposta automaticamente l'utente autenticato come proprietario se non specificato
    if book_data.get('owner_id') is None:
        book_data['owner_id'] = current_user.id
    
    # Crea un nuovo oggetto BookCreate con i dati aggiornati
    updated_book = schemas.BookCreate(**book_data)
    
    # Continua con la logica esistente
    return crud.book.create_book(db=db, book=updated_book)

@router.delete("/{book_id}", response_model=schemas.BookDelete)
def delete_book(book_id: int, db: Session = Depends(get_db)):
    deleted_book = crud.book.delete_book(db=db, book_id=book_id)
    return schemas.BookDelete(message="Book deleted successfully", book=deleted_book["book"])

@router.get("/{book_id}/cover", response_class=Response)
def get_book_cover(book_id: int, db: Session = Depends(get_db)):
    """Ottieni la copertina del libro"""
    db_book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not db_book:
        raise HTTPException(status_code=404, detail="Libro non trovato")
    if not db_book.cover_image:
        raise HTTPException(status_code=404, detail="Nessuna copertina disponibile")
    
    return Response(content=db_book.cover_image, media_type="image/jpeg")

@router.get("/{book_id}", response_model=schemas.Book)
def read_book(book_id: int, db: Session = Depends(get_db)):
    """Ottieni un singolo libro tramite ID"""
    db_book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not db_book:
        raise HTTPException(status_code=404, detail="Libro non trovato")
    
    # Imposta il flag has_cover
    setattr(db_book, "has_cover", db_book.cover_image is not None)
    
    return db_book

@router.put("/{book_id}", response_model=schemas.Book)
def update_book(book_id: int, book: schemas.BookUpdate, db: Session = Depends(get_db)):
    return crud.book.update_book(db=db, book_id=book_id, book=book)