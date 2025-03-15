from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from backend import crud, models, schemas
from backend.database import get_db

router = APIRouter()

@router.get("/", response_model=list[schemas.Book])
def read_books(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    books = crud.book.get_books(db, skip=skip, limit=limit)
    return books

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