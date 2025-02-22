from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src import crud, models, schemas
from src.database import get_db

router = APIRouter()

@router.get("/", response_model=list[schemas.Book])
def read_books(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    books = crud.book.get_books(db, skip=skip, limit=limit)
    return books

@router.post("/", response_model=schemas.Book)
def create_book(book: schemas.BookCreate, db: Session = Depends(get_db)):
    return crud.book.create_book(db=db, book=book)

@router.put("/{book_id}", response_model=schemas.Book)
def update_book(book_id: int, book: schemas.BookUpdate, db: Session = Depends(get_db)):
    return crud.book.update_book(db=db, book_id=book_id, book=book)

@router.delete("/{book_id}", response_model=schemas.BookDelete)
def delete_book(book_id: int, db: Session = Depends(get_db)):
    deleted_book = crud.book.delete_book(db=db, book_id=book_id)
    return schemas.BookDelete(message="Book deleted successfully", book=deleted_book["book"])